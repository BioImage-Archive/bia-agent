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

    poetry run bia-agent rembi-mifa-to-pagetab examples/mifa-metadata.yaml S-BIADXXX


## Dev usage

### Install pre-commit hooks

```bash
    poetry run pre-commit install
```