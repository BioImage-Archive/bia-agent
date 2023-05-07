from typing import Dict

from pydantic import BaseModel
from ruamel.yaml import YAML
from bia_rembi_models.study import Study
from bia_rembi_models.sample import Biosample
from bia_rembi_models.specimen import Specimen
from bia_rembi_models.acquisition import ImageAcquisition


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


def parse_yaml(fpath):
    yaml = YAML()
    with open(fpath) as fh:
        raw_object = yaml.load(fh)
    
    return REMBIContainer.parse_obj(raw_object)
