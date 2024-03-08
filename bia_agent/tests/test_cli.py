from typer.testing import CliRunner
from bia_agent.cli import app
from pathlib import Path
import pytest
runner = CliRunner()

ACCESSION_ID="S-BIADXXX"

@pytest.mark.parametrize(
    "rembi_file_path, cli_command, outfile",
    [
        ("examples/rembi-metadata.yaml", "rembi-to-pagetab", "examples/output/rembi-metadata_rembi-to-pagetab.tsv"),
        ("examples/mifa-metadata.yaml", "rembi-mifa-to-pagetab", "examples/output/mifa-metadata_rembi-mifa-to-pagetab.tsv"),
        ("examples/rembi-metadata-with-mifa.yaml", "rembi-mifa-to-pagetab", "examples/output/rembi-metadata-with-mifa_rembi-mifa-to-pagetab.tsv")
    ],
)
def test_cli_stdout(rembi_file_path: str, cli_command: str, outfile: str):
    
    result = runner.invoke(app, [cli_command, rembi_file_path, ACCESSION_ID])

    assert result.exit_code == 0
    assert result.stdout is not None  # Ensure some output is produced
    assert result.stdout == Path(outfile).read_text() #Veryify output is equal to files