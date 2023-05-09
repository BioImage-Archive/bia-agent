import pathlib

import typer

from .submission import submission_from_dirpath, generate_bst_submission


app = typer.Typer()



@app.command()
def show_pagetab(submission_dirpath: pathlib.Path):
    """Generate the submission PageTab and print it to the console."""

    bia_submission = submission_from_dirpath(submission_dirpath)

    bst_submission = generate_bst_submission(bia_submission)

    print(bst_submission.as_tsv())


if __name__ == "__main__":
    app()