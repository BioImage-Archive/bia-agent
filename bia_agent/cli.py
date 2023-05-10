import logging
import pathlib
from typing import Optional

import typer

from .submission import submission_from_dirpath, generate_bst_submission, generate_filelists
from .transfer import copy_single_file

logger = logging.getLogger("bia-agent")
logging.basicConfig(level=logging.INFO)


app = typer.Typer()


@app.command()
def copy_filelists(submission_dirpath: pathlib.Path):

    bia_submission = submission_from_dirpath(submission_dirpath)
    for fpath in bia_submission.generated_files_dirpath.iterdir():
        if fpath.name.startswith(bia_submission.file_list_prefix):
            copy_single_file(bia_submission, fpath)


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


if __name__ == "__main__":
    app()