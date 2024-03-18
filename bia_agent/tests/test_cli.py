from typer.testing import CliRunner
from bia_agent.cli import app, OutputFormat
from pathlib import Path
import pytest
import json
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
def test_cli_tsvout(rembi_file_path: str, cli_command: str, outfile: str):
    
    result = runner.invoke(app, [cli_command, rembi_file_path, ACCESSION_ID])

    assert result.exit_code == 0
    assert result.stdout is not None  # Ensure some output is produced
    assert result.stdout == Path(outfile).read_text() #Verify output is equal to files




@pytest.mark.parametrize(
    "yaml_file_path, json_file_path, cli_command",
    [
        ("examples/rembi-metadata.yaml", "examples/rembi-metadata.json", "rembi-to-pagetab"),
        ("examples/mifa-metadata.yaml", "examples/mifa-metadata.json", "rembi-mifa-to-pagetab"),
    ],
)
def test_json_yaml_produce_same_pagetab(yaml_file_path: str, json_file_path: str, cli_command: str):
    
    result_yaml = runner.invoke(app, [cli_command, yaml_file_path, ACCESSION_ID])
    result_json = runner.invoke(app, [cli_command, json_file_path, ACCESSION_ID])

    assert result_yaml.exit_code == 0
    assert result_json.exit_code == 0

    assert result_yaml.stdout is not None  # Ensure some output is produced
    assert result_json.stdout is not None  # Ensure some output is produced
    
    assert result_yaml.stdout ==  result_json.stdout #Verify output is the same with equivalent files




@pytest.mark.parametrize(
    "rembi_file_path, cli_command, format_option, outfile",
    [
        ("examples/rembi-metadata.yaml", "rembi-to-pagetab", "json", "examples/output/rembi-metadata_rembi-to-pagetab.json"),
        ("examples/rembi-metadata.yaml", "rembi-to-pagetab", "JSON", "examples/output/rembi-metadata_rembi-to-pagetab.json"),
        ("examples/rembi-metadata-with-mifa.yaml", "rembi-mifa-to-pagetab", "json", "examples/output/rembi-metadata-with-mifa_rembi-mifa-to-pagetab.json"),
        ("examples/rembi-metadata-with-mifa.yaml", "rembi-mifa-to-pagetab", "JSON", "examples/output/rembi-metadata-with-mifa_rembi-mifa-to-pagetab.json")
    ],
)
def test_cli_json(rembi_file_path: str, cli_command: str, format_option: str, outfile: str):
    
    result = runner.invoke(app, [cli_command, rembi_file_path, ACCESSION_ID, "-f", format_option])

    assert result.exit_code == 0
    assert result.stdout is not None  # Ensure some output is produced

    #Verify output json is equivalent
    assert json.loads(result.stdout) == json.loads(Path(outfile).read_text())

