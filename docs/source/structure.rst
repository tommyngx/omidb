==================
Database structure
==================

The database is structured into two directories:

- **images**: The medical images, in the `DICOM image format<https://en.wikipedia.org/wiki/DICOM>_`.
- **data**: The metadata, in the JSON format; 2 per client and 1 per image.

Note that the parent of these two directories will depend on how the Dropbox
account is organised (or how you've structured your local copy), but expect
something like::

    image_db/sharing/standard/

Both `images` and `data` directories share a similar tree hierarchy which, in
the case of `data`, looks like this::

    data/

      optm1/

        imagedb_optm1.json
        nbss_optm1.json
        1.2.826.0.1.3680043.9.3218.1.1.68298180.9661.1516806470059.288.0/

          1.2.826.0.1.3680043.9.3218.1.1.68298180.9661.1516806470059.291.0.json 
          ./ # More jsons

        ./ # More study folders

      optm2/

        imagedb_optm2.json
        nbss_optm2.json
        1.2.826.0.1.3680043.9.3218.1.1.6829818.9661.1516806470059.3012.0/

          1.2.826.0.1.3680043.9.3218.1.1.6829818.9661.1516806470059.3015.0.json
          ./ # More jsons

        ./ # More study folders

      ./ # More client folders

Explanation:

- There is one directory per client (patient), uniquely identified by a
  four letter prefix, e.g. `optm` (short for OPTIMAM), and a numerical index. 

- Each client directory comprises two JSON files, one containing information
  extracted from the ImageDB database, and another with data extracted from the
  NBSS database `more
  information<https://medphys.royalsurrey.nhs.uk/omidb/about-prospects/collection/>`_.

- Each client directory contains one or more directories for each study
  belonging to that client.

- Study directories are uniquely identified by the study ID, e.g.::

    1.2.826.0.1.3680043.9.3218.1.1.68298180.9661.1516806470059.288.0

- Each study directory contains a number of JSONs pertaining to that study and
  client, each with a unique ID, e.g.::

    1.2.826.0.1.3680043.9.3218.1.1.68298180.9661.1516806470059.291.0.json


The directory listing of the corresponding `images` directory is::

    images/

      optm1/

        1.2.826.0.1.3680043.9.3218.1.1.68298180.9661.1516806470059.288.0/

          1.2.826.0.1.3680043.9.3218.1.1.68298180.9661.1516806470059.291.0.dcm
          ./ # More dicom files

        ./ # More study folders

      optm2/

        1.2.826.0.1.3680043.9.3218.1.1.6829818.9661.1516806470059.3012.0/

          1.2.826.0.1.3680043.9.3218.1.1.6829818.9661.1516806470059.3015.0.dcm
          ./ # More dicoms files

        ./ # More study folders

      ./ # More client folders

The names of the client directories, study directories and files within each
study (minus the file extension) are identical to those in `data`.
