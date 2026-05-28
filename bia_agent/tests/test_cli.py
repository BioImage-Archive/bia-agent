from typer.testing import CliRunner
from bia_agent.cli import app, OutputFormat
from pathlib import Path
from ruamel.yaml import YAML
import pytest
import json
runner = CliRunner()

ACCESSION_ID="S-BIADXXX"


def write_yaml_with_mutation(tmp_path, source_fpath, mutate):
    yaml = YAML()

    with open(source_fpath) as fh:
        raw_object = yaml.load(fh)

    mutate(raw_object)

    output_fpath = tmp_path / Path(source_fpath).name
    with output_fpath.open("w") as fh:
        yaml.dump(raw_object, fh)

    return output_fpath


def result_text(result):
    return result.output

@pytest.mark.parametrize(
    "rembi_file_path, cli_command, outfile",
    [
        ("examples/rembi-metadata.yaml", "rembi-to-pagetab", "examples/output/rembi-metadata_rembi-to-pagetab.tsv"),
        ("examples/mifa-metadata.yaml", "mifa-to-pagetab", "examples/output/mifa-metadata_rembi-mifa-to-pagetab.tsv"),
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
        ("examples/mifa-metadata.yaml", "examples/mifa-metadata.json", "mifa-to-pagetab"),
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


def test_rembi_cli_rejects_missing_required_section(tmp_path):
    input_fpath = write_yaml_with_mutation(
        tmp_path,
        "examples/rembi-metadata.yaml",
        lambda raw_object: raw_object.pop("biosamples"),
    )

    result = runner.invoke(app, ["rembi-to-pagetab", str(input_fpath), ACCESSION_ID])

    assert result.exit_code == 1
    assert "Missing required section(s): biosamples" in result_text(result)


def test_rembi_mifa_cli_rejects_missing_mifa_annotations(tmp_path):
    input_fpath = write_yaml_with_mutation(
        tmp_path,
        "examples/rembi-metadata-with-mifa.yaml",
        lambda raw_object: raw_object.pop("annotations"),
    )

    result = runner.invoke(app, ["rembi-mifa-to-pagetab", str(input_fpath), ACCESSION_ID])

    assert result.exit_code == 1
    assert "Missing required section(s): annotations" in result_text(result)


def test_mifa_cli_allows_missing_version_section(tmp_path):
    input_fpath = write_yaml_with_mutation(
        tmp_path,
        "examples/mifa-metadata.yaml",
        lambda raw_object: raw_object.pop("version"),
    )

    result = runner.invoke(app, ["mifa-to-pagetab", str(input_fpath), ACCESSION_ID])

    assert result.exit_code == 0
    assert "Annotation version" not in result.stdout


def test_rembi_cli_rejects_missing_association_target(tmp_path):
    def remove_referenced_biosample(raw_object):
        raw_object["biosamples"].pop("In utero mouse embryos")

    input_fpath = write_yaml_with_mutation(
        tmp_path,
        "examples/rembi-metadata.yaml",
        remove_referenced_biosample,
    )

    result = runner.invoke(app, ["rembi-to-pagetab", str(input_fpath), ACCESSION_ID])

    assert result.exit_code == 1
    assert "Association 'experiment1' references missing biosample 'In utero mouse embryos'" in result_text(result)


def test_rembi_cli_rejects_empty_required_study_field(tmp_path):
    def empty_required_field(raw_object):
        raw_object["study"]["description"] = ""

    input_fpath = write_yaml_with_mutation(
        tmp_path,
        "examples/rembi-metadata.yaml",
        empty_required_field,
    )

    result = runner.invoke(app, ["rembi-to-pagetab", str(input_fpath), ACCESSION_ID])

    assert result.exit_code == 1
    assert "Missing or empty required study field(s): study.description" in result_text(result)
