from typing import Dict

from pydantic import BaseModel
from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError
from ruamel.yaml.parser import ParserError
from bia_rembi_models.study import Study
from bia_rembi_models.sample import Biosample
from bia_rembi_models.specimen import Specimen
from bia_rembi_models.acquisition import ImageAcquisition
from bia_mifa_models.pydantic_model import Annotations, Version
from bia_rembi_models.study_component import StudyComponent

class REMBIAssociation(BaseModel):
    biosample_id: str
    specimen_id: str
    acquisition_id: str


class REMBIContainer(BaseModel):
    study: Study
    biosamples: Dict[str, Biosample] = {}
    specimens: Dict[str, Specimen] = {}
    acquisitions: Dict[str, ImageAcquisition] = {}

    associations: Dict[str, REMBIAssociation] = {}
    annotations: Dict[str, Annotations] = {}
    version: Dict[str, Version] = {}
    study_component: Dict[str, StudyComponent] = {}


def parse_yaml(fpath):
    yaml = YAML()

    try:
        with open(fpath) as fh:
            raw_object = yaml.load(fh)
    except (ScannerError, ParserError) as e:
        exit(f"Invalid YAML: {str(e)}")


    return REMBIContainer.parse_obj(raw_object)
