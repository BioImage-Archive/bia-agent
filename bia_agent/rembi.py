from typing import Dict

from pydantic import BaseModel
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

    return REMBIContainer.parse_obj(raw_object)

def parse_json(fpath):

    try:
        with open(fpath) as file:
            raw_object = json.load(file)
    except json.JSONDecodeError as e:
        exit(f"Invalid JSON: {str(e)}")

    return REMBIContainer.parse_obj(raw_object)