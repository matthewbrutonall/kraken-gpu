import glob
import re
from xml.etree import ElementTree as ET

def get_polygons(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    # PAGE-XML uses namespaces, e.g., {http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15}Coords
    polygons = []
    for coords in root.iter():
        if coords.tag.endswith('Coords'):
            pts = coords.attrib.get('points')
            if pts:
                # 'x,y x,y x,y'
                polygons.append(pts)
    return set(polygons)

serial_files = sorted(glob.glob("/tmp/serial_xml/*.xml"))
pool_files = sorted(glob.glob("/tmp/pool_xml/*.xml"))

if len(serial_files) != 10 or len(pool_files) != 10:
    print("Missing files")
else:
    all_match = True
    for sf, pf in zip(serial_files, pool_files):
        sp = get_polygons(sf)
        pp = get_polygons(pf)
        if sp != pp:
            print(f"Mismatch in {sf}")
            print(f"Serial regions: {len(sp)}, Pool regions: {len(pp)}")
            all_match = False
    if all_match:
        print("ALL 10 PAGES MATCH EXACTLY (Polygons identical)")
