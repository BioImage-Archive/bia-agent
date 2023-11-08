import logging
import pathlib
from typing import Dict, Optional

from pydantic import BaseModel, Field
from ruamel.yaml import YAML

from .files import FileCollection
from .rembi2pagetab import rembi_container_to_pagetab
from .utils import (create_study_component,
                    create_annotations_section)
from .rembi import parse_yaml


logger = logging.getLogger("bia-agent")


class BIAAnnotations(BaseModel):
    fc_json: pathlib.Path
    description: str


class BIAFileset(BaseModel):
    fc_json: pathlib.Path
    association: str
    description: str


class BIASubmission(BaseModel):
    name: str
    filesets: Dict[str, BIAFileset] = {}
    annotations: Dict[str, BIAAnnotations] = {}
    submission_dirpath: Optional[pathlib.Path]

    file_list_prefix: str = Field("file_list", const=True)

    @property
    def files_dirpath(self):
        return self.submission_dirpath/"files"
    
    @property
    def generated_files_dirpath(self):
        return self.submission_dirpath/"generated"
    
    def create_file_structure(self):
        self.files_dirpath.mkdir(exist_ok=True, parents=True)
        self.generated_files_dirpath.mkdir(exist_ok=True, parents=True)


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


def generate_filelists(bia_submission):
    for fileset_name, fileset in bia_submission.filesets.items():
        fc_fpath = bia_submission.submission_dirpath/fileset.fc_json
        fc = FileCollection.parse_file(fc_fpath)
        file_list_infix = slugify_filename(fileset_name)
        file_list_fname = f"file_list_{file_list_infix}.tsv"
        file_list_fpath = bia_submission.generated_files_dirpath/file_list_fname

        logger.info(f"Writing file list to {file_list_fpath}")
        with open(file_list_fpath, "w") as fh:
            fh.write(fc.as_tsv(sort_keys=['Files']))    


def generate_bst_submission(bia_submission: BIASubmission, accession_id: Optional[str], skip_filelists: bool = False):
    rembi_container = parse_yaml(bia_submission.submission_dirpath/"rembi-metadata.yaml")

    root_path = f"{bia_submission.submission_dirpath.name}/files"
    bst_submission = rembi_container_to_pagetab(rembi_container, accession_id=accession_id, root_path=root_path)
    bia_submission.create_file_structure()

    if skip_filelists:
        return bst_submission
    
    for fileset_name, fileset in bia_submission.filesets.items():
        fc_fpath = bia_submission.submission_dirpath/fileset.fc_json
        fc = FileCollection.parse_file(fc_fpath)
        file_list_infix = slugify_filename(fileset_name)
        file_list_fname = f"file_list_{file_list_infix}.tsv"
        file_list_fpath = bia_submission.generated_files_dirpath/file_list_fname

        logger.info(f"Writing file list to {file_list_fpath}")
        with open(file_list_fpath, "w") as fh:
            fh.write(fc.as_tsv(sort_keys=['Files']))

        association = rembi_container.associations[fileset.association]

        study_component = create_study_component(
            name=fileset_name,
            description=fileset.description,
            association=association,
            file_list_fname=file_list_fname
        )

        bst_submission.section.subsections.append(study_component)

    for annotations_name, annotations in bia_submission.annotations.items():
        logger.info(f"Processing annotations: {annotations_name}")

        fc_fpath = bia_submission.submission_dirpath/annotations.fc_json
        fc = FileCollection.parse_file(fc_fpath)
        file_list_infix = slugify_filename(annotations_name)
        file_list_fname = f"file_list_{file_list_infix}.tsv"
        file_list_fpath = bia_submission.generated_files_dirpath/file_list_fname

        logger.info(f"Writing file list to {file_list_fpath}")
        with open(file_list_fpath, "w") as fh:
            fh.write(fc.as_tsv(sort_keys=['Files']))

        annotations_section = create_annotations_section(
            name=annotations_name,
            description=annotations.description,
            file_list_fname=file_list_fname
        )

        bst_submission.section.subsections.append(annotations_section)
        
    return bst_submission