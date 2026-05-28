BIA Agent
=========

A Python package including a library/CLI interface for preparing submissions to the BioImage Archive.

Converting REMBI YAML to PageTab
--------------------------------

If this package is installed, run, e.g:

    bia-agent rembi-to-pagetab examples/rembi-metadata.yaml S-BIADXXX

Using poetry:

    poetry run bia-agent rembi-to-pagetab examples/rembi-metadata.yaml S-BIADXXX

Converting REMBI with MIFA annotations YAML to PageTab
------------------------------------------------------

Using poetry:

    poetry run bia-agent rembi-mifa-to-pagetab examples/rembi-metadata-with-mifa.yaml S-BIADXXX

Converting MIFA annotations YAML to PageTab
-------------------------------------------

Using poetry:

    poetry run bia-agent mifa-to-pagetab examples/mifa-metadata.yaml S-BIADXXX

Converting giga-EM spreadsheet to PageTab
-------------------------------------------

Using poetry:

    poetry run bia-agent gigaem-to-pagetab examples/giga-em_study.csv examples/giga-em_images.csv examples/giga-em_annotations.csv S-BIADXXX


## Dev usage

### Install pre-commit hooks

```bash
    poetry run pre-commit install
```
