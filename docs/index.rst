kraken-gpu
==========

.. toctree::
   :hidden:
   :maxdepth: 2

   introduction_to_atr
   getting_started
   user_guide/index
   api/index
   changelog

``kraken-gpu`` is an independent Apache-2.0 fork focused on faster default BLLA
page segmentation. It keeps Kraken's Python import namespace and model/plugin
metadata for compatibility, but publishes the command-line entry point as
``kraken-gpu`` to avoid confusion with the original Kraken project.

This fork is not a GPU geometry engine. The neural network and parent-only
Sato filter run on GPU; the line polygon work remains stock Shapely.

Features
========

This fork's main changes are:

  - Page-level process pool for ``kraken-gpu segment`` with ``-w`` workers.
  - Parent-process GPU Sato matching scikit-image output.
  - Worker processes skip CUDA and keep OpenMP/BLAS thread pools pinned.
  - ``-w > 1`` is limited to the default single-model BLLA path.

Integrations
============

The underlying codebase remains compatible with the broader Kraken ecosystem:

*   `eScriptorium <https://www.escriptorium.fr/>`_: A web-based platform for annotating, transcribing, and training ATR models, tightly integrating kraken.
*   `OCR4all <https://ocr4all.org/>`_: A comprehensive ATR framework designed for historical documents, offering a user-friendly interface for various ATR tasks.
*   `OCR-D suite <https://ocr-d.de/>`_: A collection of tools for ATR-related tasks, aiming to build a full-stack ATR workflow for historical prints.
*   `arkindex by Teklia <https://arkindex.teklia.com/>`_: A platform for large-scale document analysis and indexing with kraken support through a plugin.


License
=======

Apache-2.0. This fork derives from Kraken by Benjamin Kiessling and
contributors.
