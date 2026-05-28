from typing import Dict

from pydantic import BaseModel, ValidationError
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.parser import ParserError
from bia_rembi_models.study import Study
from bia_rembi_models.sample import Biosample
from bia_rembi_models.specimen import Specimen
from bia_rembi_models.acquisition import ImageAcquisition
from bia_rembi_models.correlation import ImageCorrelation
from bia_rembi_models.analysis import ImageAnalysis
from bia_mifa_models.pydantic_model import Annotations, Version
from bia_rembi_models.study_component import StudyComponent
from pathlib import Path
import json

class REMBIAssociation(BaseModel):
    biosample_id: str
    specimen_id: str
    acquisition_id: str
    correlation_id: str = None
    analysis_id: str = None


class REMBIContainer(BaseModel):
    study: Study
    biosamples: Dict[str, Biosample] = {}
    specimens: Dict[str, Specimen] = {}
    acquisitions: Dict[str, ImageAcquisition] = {}
    correlations: Dict[str, ImageCorrelation] = {}
    analysis: Dict[str, ImageAnalysis] = {}

    associations: Dict[str, REMBIAssociation] = {}
    annotations: Dict[str, Annotations] = {}
    version: Dict[str, Version] = {}
    study_component: Dict[str, StudyComponent] = {}


class REMBIValidationError(ValueError):
    pass


STUDY_REQUIRED_FIELDS = (
    "title",
    "description",
    "private_until_date",
    "keywords",
    "authors",
    "rembi_version",
)

REMBI_REQUIRED_SECTIONS = (
    "biosamples",
    "specimens",
    "acquisitions",
    "study_component",
    "associations",
)

MIFA_REQUIRED_SECTIONS = (
    "annotations",
)

MIFA_REQUIRED_ANNOTATION_FIELDS = (
    "annotation_overview",
    "annotation_type",
    "annotation_method",
)

ASSOCIATION_TARGETS = (
    ("biosample_id", "biosamples", "biosample"),
    ("specimen_id", "specimens", "specimen"),
    ("acquisition_id", "acquisitions", "acquisition"),
    ("correlation_id", "correlations", "correlation"),
    ("analysis_id", "analysis", "analysis"),
)


def validate_rembi_metadata(container: REMBIContainer):
    errors = []
    _validate_required_study_fields(container, errors)
    _validate_required_sections(container, REMBI_REQUIRED_SECTIONS, errors)
    _validate_study_component_associations(container, errors)
    _validate_association_targets(container, errors)
    _raise_validation_errors(errors)


def validate_mifa_metadata(container: REMBIContainer):
    errors = []
    _validate_required_study_fields(container, errors)
    _validate_required_sections(container, MIFA_REQUIRED_SECTIONS, errors)
    _validate_mifa_fields(container, errors)
    _validate_annotation_versions(container, errors)
    _raise_validation_errors(errors)


def validate_rembi_mifa_metadata(container: REMBIContainer):
    errors = []
    _validate_required_study_fields(container, errors)
    _validate_required_sections(container, REMBI_REQUIRED_SECTIONS + MIFA_REQUIRED_SECTIONS, errors)
    _validate_study_component_associations(container, errors)
    _validate_association_targets(container, errors)
    _validate_mifa_fields(container, errors)
    _validate_annotation_versions(container, errors)
    _raise_validation_errors(errors)


def _validate_required_study_fields(container, errors):
    missing_fields = [
        f"study.{field_name}"
        for field_name in STUDY_REQUIRED_FIELDS
        if _is_empty_required_value(getattr(container.study, field_name, None))
    ]

    if missing_fields:
        errors.append("Missing or empty required study field(s): " + ", ".join(missing_fields))


def _validate_required_sections(container, section_names, errors):
    missing_sections = [
        section_name
        for section_name in section_names
        if not getattr(container, section_name)
    ]

    if missing_sections:
        errors.append("Missing required section(s): " + ", ".join(missing_sections))


def _validate_study_component_associations(container, errors):
    study_component_ids = set(container.study_component)
    association_ids = set(container.associations)

    for study_component_id in sorted(study_component_ids - association_ids):
        errors.append(f"Study component '{study_component_id}' is missing a matching association")

    for association_id in sorted(association_ids - study_component_ids):
        errors.append(f"Association '{association_id}' does not match a study component")


def _validate_association_targets(container, errors):
    for association_id, association in container.associations.items():
        for field_name, section_name, label in ASSOCIATION_TARGETS:
            target_id = getattr(association, field_name)
            if not target_id:
                continue

            target_section = getattr(container, section_name)
            if target_id not in target_section:
                errors.append(f"Association '{association_id}' references missing {label} '{target_id}'")


def _validate_mifa_fields(container, errors):
    for annotation_id, annotation in container.annotations.items():
        missing_fields = [
            f"annotations.{annotation_id}.{field_name}"
            for field_name in MIFA_REQUIRED_ANNOTATION_FIELDS
            if _is_empty_required_value(getattr(annotation, field_name, None))
        ]

        if missing_fields:
            errors.append("Missing or empty required MIFA field(s): " + ", ".join(missing_fields))


def _validate_annotation_versions(container, errors):
    annotation_ids = set(container.annotations)
    version_ids = set(container.version)

    for version_id in sorted(version_ids - annotation_ids):
        errors.append(f"Version '{version_id}' does not match an annotation")


def _is_empty_required_value(value):
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, dict, set)):
        return not value
    return False


def _raise_validation_errors(errors):
    if errors:
        raise REMBIValidationError("\n".join(errors))


def parse(fpath):
    if not Path(fpath).is_file():
        exit(f"{fpath} is not a file")

    
    match Path(fpath).suffix:
        case '.json':
            return parse_json(fpath)
        case '.yaml':
            return parse_yaml(fpath)
        case _:
            exit(f'{fpath} is not a json or yaml')

            
def parse_yaml(fpath):
    yaml = YAML()

    try:
        with open(fpath) as fh:
            raw_object = yaml.load(fh)
    except (ScannerError, ParserError) as e:
        exit(f"Invalid YAML: {str(e)}")

    try:
        return REMBIContainer.parse_obj(raw_object)
    except ValidationError as e:
        raise REMBIValidationError(str(e)) from e

def parse_json(fpath):

    try:
        with open(fpath) as file:
            raw_object = json.load(file)
    except json.JSONDecodeError as e:
        exit(f"Invalid JSON: {str(e)}")

    try:
        return REMBIContainer.parse_obj(raw_object)
    except ValidationError as e:
        raise REMBIValidationError(str(e)) from e
