import os
import multiprocessing
import queue

def setup_thread_pinning():
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    import torch
    torch.set_num_threads(1)

def cpu_worker(in_queue, out_queue):
    setup_thread_pinning()
    
    from kraken.lib.vgsl.spred import vec_regions, vec_lines, scale_regions
    from kraken.containers import BaselineLine, Segmentation
    import shapely.geometry as geom
    from kraken.lib.segmentation import is_in_region, polygonal_reading_order
    from kraken import serialization
    import uuid

    while True:
        job = in_queue.get()
        if job is None:
            break
            
        path, out_file, rets, inf_config, user_metadata, im_size, output_mode, output_template, steps, subline_segmentation = job
        try:
            _regions = vec_regions(**rets)
            regions = {}
            for reg_key, reg_val in _regions.items():
                regions.setdefault(reg_key, [])
                regions[reg_key].extend(reg_val)

            line_regs = []
            suppl_obj = []
            for cls, regs in _regions.items():
                line_regs.extend(regs)
                if rets['bounding_regions'] is not None and cls in rets['bounding_regions']:
                    suppl_obj.extend(regs)

            suppl_obj = scale_regions([x.boundary for x in suppl_obj], 1 / rets['scale'])
            line_regs = scale_regions([x.boundary for x in line_regs], 1 / rets['scale'])

            lines = vec_lines(**rets,
                              regions=line_regs,
                              text_direction=inf_config['text_direction'],
                              suppl_obj=suppl_obj,
                              topline=bool(user_metadata.get('topline', False)),
                              raise_on_error=inf_config.get('raise_on_error', False))

            script_detection = len(rets['cls_map']['baselines']) > 1
            blls = []
            _shp_regs = {}
            for reg_type, rgs in regions.items():
                for reg in rgs:
                    _shp_regs[reg.id] = geom.Polygon(reg.boundary)

            for line in lines:
                l_regs = []
                for reg_id, reg in _shp_regs.items():
                    line_ls = geom.LineString(line['baseline'])
                    if is_in_region(line_ls, reg):
                        l_regs.append(reg_id)
                blls.append(BaselineLine(id=f"_{uuid.uuid4()}", baseline=line['baseline'], boundary=line['boundary'], tags=line['tags'], regions=l_regs))

            if blls:
                all_regions = [reg for rgs in regions.values() for reg in rgs]
                ro = polygonal_reading_order(lines=blls,
                                             regions=all_regions,
                                             text_direction=inf_config['text_direction'][-2:])
                blls = [blls[idx] for idx in ro]

            seg = Segmentation(text_direction=inf_config['text_direction'],
                                imagename=path,
                                type='baselines',
                                lines=blls,
                                regions=regions,
                                script_detection=script_detection,
                                line_orders=[])
            
            if output_mode != 'native':
                xml_str = serialization.serialize(seg, 
                                                image_size=im_size, 
                                                template=output_template, 
                                                template_source='custom' if output_mode == 'template' else 'native',
                                                processing_steps=steps,
                                                sub_line_segmentation=subline_segmentation)
            else:
                import dataclasses, json
                xml_str = json.dumps(dataclasses.asdict(seg))

            out_queue.put((path, out_file, xml_str, None))
        except Exception as e:
            out_queue.put((path, out_file, None, str(e)))

def run_batch(input_pairs, model, config, ctx):
    import torch
    from kraken.lib.util import open_image
    import click

    workers = ctx.meta.get('workers', 1)
    if workers < 1:
        workers = 1

    n_seg = len(getattr(model, 'seg_models', []) or [])
    n_ro = len(getattr(model, 'ro_models', []) or [])
    if n_seg > 1 or n_ro:
        raise click.UsageError(
            '-w > 1 only runs the default single-model BLLA path '
            '(one segmentation model, polygonal reading order). '
            'Use -w 1 for multiple segmentation models or a neural reading-order model.'
        )

    click.echo(f'Running GPU batch segmentation on {len(input_pairs)} files with {workers} workers...')

    manager = multiprocessing.Manager()
    in_queue = manager.Queue(maxsize=16)
    out_queue = manager.Queue()
    
    pool = multiprocessing.Pool(workers, initializer=setup_thread_pinning)
    async_results = []
    for _ in range(workers):
        async_results.append(pool.apply_async(cpu_worker, (in_queue, out_queue)))

    def put_input(item):
        while True:
            for res in async_results:
                if res.ready():
                    res.get()
            try:
                in_queue.put(item, timeout=5)
                return
            except queue.Full:
                continue
        
    inf_config = {
        'text_direction': getattr(config, 'text_direction', 'horizontal-lr'),
        'raise_on_error': False
    }
    user_metadata = model.seg_models[0].user_metadata if hasattr(model, 'seg_models') and len(model.seg_models) > 0 else getattr(model, 'user_metadata', {})
    
    output_mode = ctx.meta.get('output_mode', 'native')
    output_template = ctx.meta.get('output_template', 'native')
    steps = ctx.meta.get('steps', [])
    subline_segmentation = ctx.meta.get('subline_segmentation', True)

    import threading
    consumer_error = []
    
    def consumer():
        processed = 0
        while processed < len(input_pairs):
            try:
                in_file, out_file, xml_str, err = out_queue.get(timeout=5)
            except queue.Empty:
                for res in async_results:
                    if res.ready():
                        try:
                            res.get()
                        except Exception as e:
                            consumer_error.append(e)
                            return
                continue
            if xml_str is not None:
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                click.echo(f'[\u2713] {in_file} -> {out_file}')
            else:
                click.echo(f'[\u2717] {in_file} - {err}')
            processed += 1

    consumer_thread = threading.Thread(target=consumer, daemon=True)
    consumer_thread.start()

    from kraken.lib.segmentation import apply_sato_heatmap

    inner_model = model.seg_models[0]
    inner_model.prepare_for_inference(config)
    with torch.inference_mode():
        for in_file, out_file in input_pairs:
            in_file = str(in_file)
            out_file = str(out_file)
            try:
                im = open_image(in_file)
                with inner_model._fabric.init_tensor():
                     rets = inner_model._compute_segmentation_map(im)
                rets['heatmap'] = apply_sato_heatmap(rets['heatmap'], rets['cls_map'])
                rets['sato_applied'] = True
                put_input((in_file, out_file, rets, inf_config, user_metadata, im.size, output_mode, output_template, steps, subline_segmentation))
            except Exception as e:
                out_queue.put((in_file, out_file, None, str(e)))
            
    for _ in range(workers):
        put_input(None)
        
    consumer_thread.join()
    if consumer_error:
        pool.terminate()
        pool.join()
        raise consumer_error[0]
    pool.close()
    pool.join()
