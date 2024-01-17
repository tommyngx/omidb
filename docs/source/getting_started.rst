=================
Install and usage
=================

`omidb` is a Python 3 command-line interface and package for parsing and
interacting with the `OPTIMAM Mammography Image Database
<https://medphys.royalsurrey.nhs.uk/omidb/>`_.  Unless you have authorised
access to the official database, it is assumed that you have downloaded the
database (most likely a subset of it) via the `OMI-DB Sync Tool
<https://www.dropbox.com/s/5fevudqwny0t50b/OMI-DB-Sync-Tool_UserGuide.pdf?dl=1>`_.
For an overview of the database, see  :doc:`structure`.

CLI
===

A simple command-line interface (CLI), ``omidb``, has been developed to
automate useful data extraction tasks commonly implemented by the hands of
researchers working with the database.

The CLI is currently limited to one (very useful) command, ``summarise``, which
can be applied to your local copy of OMI-DB::

    omidb summarise <path-to-omidb> <path-to-output-csv-file>

This will pass over the JSON data (within the `data` directory of OMI-DB), and
generate a CSV file that summarises the database, at the image level. For
example, the majority of images will be associated with a series, medical
procedure, study, NBSS episode and client. The command also extracts a few
useful DICOM tags, such as the manufacturer of the device, and the intent of
presentation.  This does not require access to the DICOM images themselves.

The ``--clients-file <my-client-list.txt>`` option can be added to specify a
list of clients to parse, rather than traversing the entire database. It should
point to the path of a text file holding one line per client::

    # my-client-list.txt
    demd1
    demd2

The ``omidb`` package logger provides detailed information about the parsing
process, e.g. studies that can't be linked to an event, so, if interested, we
recommend you route logging to a file by adding the ``--log-file
<path-to-log-file>`` option.

Package Usage
=============

Import the package::

    >>> import omidb

The following code iteratively parses clients ``demd8482`` and ``demd11022`` from the database::

    >>> db = omidb.DB('./OMI-DB', clients=['demd8482', 'demd11022'])
    >>> clients = [client for client in db]
    >>> [print(client.id) for client in clients]
    demd11022
    demd8482

The hierarchical structure of OMI-DB is modelled by nested objects::

    >>> clients[0].episodes[0].studies[0].series[0].images[0].marks

NBSS data attributes are available through class members::

    >>> print(clients[0].classification.value)
    Noraml
    >>> print(clients[0].episodes[0].value)
    RR

Access dicom properties for an image (using `pydicom <https://github.com/pydicom/pydicom>`_)::

	>>> print(clients[0].episodes[0].studies[0].series[0].images[0].dcm.PresentationIntentType)
	FOR PRESENTATION

or via provided JSON representations of the DICOM headers (so no need for the
DICOMs themselves)::

    >>> print(clients[0].episodes[0].studies[0].series[0].images[0].attributes['00080068'])
    {'vr': 'CS', 'Value': ['FOR PRESENTATION']}

Plot individual images (via `matplotlib <https://matplotlib.org/>`_) and images within a series::

    >>> clients[0].episodes[0].studies[0].series[0].images[0].plot()
    >>> clients[0].episodes[0].studies[0].series[0].plot()

Use ``FilterImages`` to perform inplace, recursive dicom property filtering over images::

    >>> image_filter = omidb.filters.FilterImages.dicom_filter(
        {'PresentationIntentType': ['FOR PROCESSING']})
    >>> image_filter(clients[0])  # In-place filtering


See :doc:`omidb` for API documentation.


Installing
==========

You will need version >=3.7 of Python.

For the CLI only, we recommend `pipx <https://pipxproject.github.io/pipx/>`_::

    pipx install omidb

To install the package in your project::

    poetry add omidb

or::

    pip install omidb

For development::

    git clone https://bitbucket.org/scicomcore/omi-db.git
    poetry install --dev

To build the documentation::

    cd ./docs
    poetry run make html
