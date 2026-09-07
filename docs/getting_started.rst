.. _getting_started:

Getting Started
===============

This guide provides a brief overview of how to install and use ``kraken-gpu``.

Installation
------------

Use a virtual environment. On systems with a custom PyTorch build, create the
environment with ``--system-site-packages`` and install this fork with
``--no-deps`` so pip does not replace the system Torch wheel.

.. code-block:: console

   $ python3 -m venv --system-site-packages .venv
   $ . .venv/bin/activate
   $ pip install -e . --no-deps

For a normal environment where pip may resolve dependencies:

.. code-block:: console

   $ python3 -m venv .venv
   $ . .venv/bin/activate
   $ pip install .

If you want direct PDF and multi-image TIFF/JPEG2000 support, install the
``pdf`` extra:

.. code-block:: console

   $ pip install .[pdf]

Model Retrieval
---------------

After installation, you'll need a model to process your documents. In the
``kraken`` Python namespace,
models are pre-trained files that contain the knowledge for a specific task,
such as identifying the layout of a page or recognizing characters in a
particular script.

The model repository can be accessed
from the command line. To list all available models, run:

.. code-block:: console

    $ kraken-gpu list

To download a model, use the `get` command with the model's DOI. For example,
to download the default model for printed French text, run:

.. code-block:: console

  $ kraken-gpu get 10.5281/zenodo.10592716

For more information on how to interact with the model repository, please refer
to the :doc:`user_guide/models` section of the user guide.

The ATR Workflow
----------------

Automatic text recognition is a multi-step process that transforms an image of
a document into a text file. In ``kraken-gpu``, this process is broken down into a
sequence of chainable commands, each performing a specific task.

The three main steps in a typical ATR workflow are:

1.  **Layout Analysis (Segmentation):** This step identifies the regions and
    lines of text on the page. In ``kraken-gpu``, this is done with the `segment`
    command.
2.  **Text Recognition (ATR):** This step transcribes the text from the line
    images identified in the previous step. In ``kraken-gpu``, this is done with the
    `ocr` command.
3.  **Serialization:** This step saves the output of the previous steps in a
    structured format, such as plain text, ALTO, or PageXML. This is handled
    by the output options of the ``kraken-gpu`` command.

Models are essential to this workflow, as they provide the specific knowledge
for layout analysis and text recognition. They are integrated into the ``kraken``
workflow as parameters for the `segment` and `ocr` commands. The choice of
model is crucial for achieving good results, as a model trained on a specific
type of material will perform best on similar material.

Here is a quick example of a complete workflow:

.. raw:: html
    :file: _static/kraken_workflow.svg

Recognizing text on an image using the default parameters, including page
segmentation:

.. code-block:: console

  $ kraken-gpu -i image.tif image.txt segment -bl ocr -m catmus-print-fondue-large.mlmodel

In this example, `segment` performs the layout analysis, and `ocr` performs the
text recognition using the `catmus-print-fondue-large.mlmodel`. The final
transcription is saved to `image.txt`.
