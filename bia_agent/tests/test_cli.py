from typer.testing import CliRunner
from bia_agent.cli import app
import pytest
runner = CliRunner()

@pytest.mark.parametrize(
    "rembi_file_path, accession_id",
    [
        ("examples/rembi-metadata.yaml", "S-BIADXX"),
    ],
)
def test_rembi(rembi_file_path: str, accession_id: str):
    result = runner.invoke(app, ["rembi-to-pagetab", rembi_file_path, accession_id])
    assert result.exit_code == 0
    assert result.stdout is not None  # Ensure some output is produced
