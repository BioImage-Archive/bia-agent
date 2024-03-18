import logging
import pathlib
from typing import Optional
from typing_extensions import Annotated
from enum import Enum

import typer

from .biostudies import Submission
from .files import FileCollection
from .submission import submission_from_dirpath, generate_bst_submission, generate_filelists
from .transfer import copy_single_file, copy_all, verify
from .rembi import parse
from .rembi2pagetab import rembi_container_to_pagetab
from .mifa2pagetab import rembi_mifa_container_to_pagetab, mifa_container_to_pagetab


logger = logging.getLogger("bia-agent")
logging.basicConfig(level=logging.INFO)


app = typer.Typer()

class OutputFormat(str, Enum):
    TSV = 'tsv'
    JSON = 'json'


@app.command()
def copy_all_files(submission_dirpath: pathlib.Path, file_collection_name: str):

    bia_submission = submission_from_dirpath(submission_dirpath)

    fname = f"{file_collection_name}_fc.json"
    fc = FileCollection.parse_file(submission_dirpath/fname)

    logging.info(f"Copying files in collection {file_collection_name}")
    copy_all(bia_submission.name, fc)


@app.command()
def verify_files(submission_dirpath: pathlib.Path, file_collection_name: str):

    bia_submission = submission_from_dirpath(submission_dirpath)

    fname = f"{file_collection_name}_fc.json"
    fc = FileCollection.parse_file(submission_dirpath/fname)

    logging.info(f"Verifying files in collection {file_collection_name}")
    verify(bia_submission.name, fc)


@app.command()
def init(submission_dirpath: pathlib.Path):
    """Create the initial submission structure at the given path, including the
    submission and REMBI metadata files."""

    raise NotImplementedError


@app.command()
def copy_filelists(submission_dirpath: pathlib.Path):
    """Copy generated filelists to BioStudies user space."""

    bia_submission = submission_from_dirpath(submission_dirpath)
    for fpath in bia_submission.generated_files_dirpath.iterdir():
        if fpath.name.startswith(bia_submission.file_list_prefix):
            copy_single_file(bia_submission, fpath)


@app.command()
def generate_filelist_template(submission_dirpath: pathlib.Path):
    bia_submission = submission_from_dirpath(submission_dirpath)

    fc = FileCollection.from_fs_path(submission_dirpath/"files", ".")

    print(fc.as_tsv(sort_keys=['Files']))


@app.command()
def generate_file_collection(submission_dirpath: pathlib.Path, fc_name: str):
    fc = FileCollection.from_fs_path(submission_dirpath/"files", ".")

    output_fname = f"{fc_name}_fc.json"
    with open(submission_dirpath/output_fname, "w") as fh:
        fh.write(fc.json(indent=2))


@app.command()
def generate_filelists(submission_dirpath: pathlib.Path):
    pass


@app.command()
def process(submission_dirpath: pathlib.Path):

    bia_submission = submission_from_dirpath(submission_dirpath)
    bst_submission = generate_bst_submission(bia_submission)


@app.command()
def create_structure(submission_dirpath: pathlib.Path):
    
    bia_submission = submission_from_dirpath(submission_dirpath)
    bia_submission.create_file_structure()


@app.command()
def show_pagetab(submission_dirpath: pathlib.Path, accession_id: str = "", skip_filelists: bool = False):
    """Generate the submission PageTab and print it to the console."""

    bia_submission = submission_from_dirpath(submission_dirpath)

    bst_submission = generate_bst_submission(bia_submission, accession_id=accession_id, skip_filelists=skip_filelists)

    print(bst_submission.as_tsv())


@app.command()
def check_pagetab_json(json_fpath: pathlib.Path):
    """Check pagetab JSON validity by trying to parse it."""

    submission = Submission.parse_file(json_fpath)

    print(submission.as_tsv())


@app.command()
def rembi_to_pagetab(
    rembi_fpath: pathlib.Path, 
    accession_id: str,
    outputFormat: Annotated[OutputFormat, typer.Option("-f", case_sensitive=False)] = OutputFormat.TSV.value
):
    rembi_container = parse(rembi_fpath)

    bst_submission = rembi_container_to_pagetab(rembi_container, accession_id=accession_id, root_path=None)

    if outputFormat == OutputFormat.TSV:
        print(bst_submission.as_tsv())
    elif outputFormat == OutputFormat.JSON:
        print(bst_submission.json())


@app.command()
def rembi_mifa_to_pagetab(
    rembi_mifa_fpath: pathlib.Path, 
    accession_id: str,
    outputFormat: Annotated[OutputFormat, typer.Option("-f", case_sensitive=False)] = OutputFormat.TSV.value
):
    rembi_mifa_container = parse(rembi_mifa_fpath)

    bst_submission = rembi_mifa_container_to_pagetab(rembi_mifa_container, accession_id=accession_id, root_path=None)
    
    if outputFormat == OutputFormat.TSV:
        print(bst_submission.as_tsv())
    elif outputFormat == OutputFormat.JSON:
        print(bst_submission.json())

@app.command()
def mifa_to_pagetab(
    mifa_fpath: pathlib.Path, 
    accession_id: str,
    outputFormat: Annotated[OutputFormat, typer.Option("-f", case_sensitive=False)] = OutputFormat.TSV.value
):
    mifa_container = parse(mifa_fpath)

    bst_submission = mifa_container_to_pagetab(mifa_container, accession_id=accession_id, root_path=None)
    
    if outputFormat == OutputFormat.TSV:
        print(bst_submission.as_tsv())
    elif outputFormat == OutputFormat.JSON:
        print(bst_submission.json())


if __name__ == "__main__":
    app()