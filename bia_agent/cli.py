import pathlib

import typer

app = typer.Typer()


@app.command()
def validate_submission(submission_dirpath: pathlib.Path):

    submission_file_fpath = submission_dirpath / "submission.yaml"


if __name__ == "__main__":
    app()