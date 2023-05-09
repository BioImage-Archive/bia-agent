import pathlib
from typing import Dict, Optional

from pydantic import BaseModel
from ruamel.yaml import YAML

from .files import FileCollection
from .rembi2pagetab import create_study_component, rembi_container_to_pagetab
from .rembi import parse_yaml


class BIAFileset(BaseModel):
    fc_json: pathlib.Path
    association: str
    description: str


class BIASubmission(BaseModel):
    name: str
    filesets: Dict[str, BIAFileset]
    submission_dirpath: Optional[pathlib.Path]


def submission_from_dirpath(submission_dirpath: pathlib.Path):
    
    submission_file_fpath = submission_dirpath / "submission.yaml"

    yaml = YAML()

    with open(submission_file_fpath) as fh:
        raw_object = yaml.load(fh)

    bia_submission = BIASubmission.parse_obj(raw_object)
    bia_submission.submission_dirpath = submission_dirpath

    return bia_submission


def slugify_filename(input_str):
    """Convert a descriptive string into a standardised filename."""
    return input_str.replace(" ", "_").lower()


def generate_bst_submission(bia_submission):
    rembi_container = parse_yaml(bia_submission.submission_dirpath/"rembi-metadata.yaml")

    root_path = f"{bia_submission.submission_dirpath.name}/files"
    bst_submission = rembi_container_to_pagetab(rembi_container, root_path=root_path)

    for fileset_name, fileset in bia_submission.filesets.items():
        fc_fpath = bia_submission.submission_dirpath/fileset.fc_json
        fc = FileCollection.parse_file(fc_fpath)
        file_list_prefix = slugify_filename(fileset_name)
        file_list_fname = f"{file_list_prefix}.tsv"
        file_list_fpath = bia_submission.submission_dirpath/"files"/file_list_fname

        with open(file_list_fpath, "w") as fh:
            fh.write(fc.as_tsv(sort_keys=['Files']))

        association = rembi_container.associations[fileset.association]

        study_component = create_study_component(
            name=fileset_name,
            description="Some description",
            association=association,
            file_list_fname=file_list_fname
        )

        bst_submission.section.subsections.append(study_component)

    return bst_submission