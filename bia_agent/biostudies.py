import logging
import pathlib
import datetime
from typing import List, Union, Optional

import requests
from pydantic import BaseModel, parse_raw_as


logger = logging.getLogger(__name__)


STUDY_URL_TEMPLATE = "https://www.ebi.ac.uk/biostudies/api/v1/studies/{accession}"
FLIST_URI_TEMPLATE = (
    "https://www.ebi.ac.uk/biostudies/files/{accession_id}/{flist_fname}"
)
FILE_URI_TEMPLATE = (
    "https://www.ebi.ac.uk/biostudies/files/{accession_id}/{relpath}"
)


class AttributeDetail(BaseModel):
    name: str
    value: str


class Attribute(BaseModel):
    name: str
    value: Optional[str]
    reference: bool = False
    nmqual: List[AttributeDetail] = []
    valqual: List[AttributeDetail] = []

    def as_tsv(self):
        # None values serialize as 'None' in the submission pagetab which may be misleading (e.g. authors with Role: 'None')
        value_serialised = self.value if self.value else ""

        if self.reference:
            tsv_rep = f"<{self.name}>\t{value_serialised}\n"
        else:
            tsv_rep = f"{self.name}\t{value_serialised}\n"

        return tsv_rep

# File List


class File(BaseModel):
    path: pathlib.Path
    size: int
    attributes: List[Attribute] = []


class Link(BaseModel):
    url: str
    attributes: List[Attribute] = []

    def as_tsv(self):
        tsv_rep = "\n"
        tsv_rep += f"Link\t{self.url}\n"
        tsv_rep += "".join([attr.as_tsv() for attr in self.attributes])

        return tsv_rep


class Section(BaseModel):
    type: str
    accno: Optional[str]
    attributes: List[Attribute] = []
    subsections: List["Section"] = []
    links: List[Link] = []
    files: List[Union[File, List[File]]] = []

    def as_tsv(self, parent_accno=None):
        tsv_rep = "\n"

        accno_str = self.accno if self.accno else ""
        if parent_accno:
            tsv_rep += f"{self.type}\t{accno_str}\t{parent_accno}"
        else:
            if self.accno:
                tsv_rep += f"{self.type}\t{accno_str}"
            else:
                tsv_rep += f"{self.type}"

        tsv_rep += "\n"

        tsv_rep += "".join([attr.as_tsv() for attr in self.attributes])
        tsv_rep += "".join([link.as_tsv() for link in self.links])
        tsv_rep += "".join([section.as_tsv(self.accno) for section in self.subsections])

        return tsv_rep


class Submission(BaseModel):
    accno: Optional[str]
    section: Section
    attributes: List[Attribute]

    def as_tsv(self) -> str:
        tsv_rep = f"Submission"
        if self.accno:
            tsv_rep += f"\t{self.accno}"
        tsv_rep += "\n"

        tsv_rep += "".join([attr.as_tsv() for attr in self.attributes])
        tsv_rep += self.section.as_tsv()

        return tsv_rep




# API search classes


class StudyResult(BaseModel):
    accession: str
    title: str
    author: str
    links: int
    files: int
    release_date: datetime.date
    views: int
    isPublic: bool


class QueryResult(BaseModel):
    page: int
    pageSize: int
    totalHits: int
    isTotalHitsExact: bool
    sortBy: str
    sortOrder: str
    hits: List[StudyResult]


# API functions


def load_submission(accession_id: str) -> Submission:

    url = STUDY_URL_TEMPLATE.format(accession=accession_id)
    logger.info(f"Fetching submission from {url}")
    r = requests.get(url)

    assert r.status_code == 200

    submission = Submission.parse_raw(r.content)

    return submission


def attributes_to_dict(attributes: List[Attribute]) -> dict:

    return {attr.name: attr.value for attr in attributes}


def find_file_lists_in_section(section, flists) -> list:

    attr_dict = attributes_to_dict(section.attributes)

    if "File List" in attr_dict:
        flists.append(attr_dict["File List"])

    for subsection in section.subsections:
        find_file_lists_in_section(subsection, flists)

    return flists


def find_file_lists_in_submission(submission: Submission):

    return find_file_lists_in_section(submission.section, [])


def flist_from_flist_fname(accession_id: str, flist_fname: str):

    flist_url = FLIST_URI_TEMPLATE.format(
        accession_id=accession_id, flist_fname=flist_fname
    )

    r = requests.get(flist_url)
    logger.info(f"Fetching file list from {flist_url}")
    assert r.status_code == 200

    fl = parse_raw_as(List[File], r.content)

    return fl


def file_uri(accession_id: str, file: File):

    return FILE_URI_TEMPLATE.format(
        accession_id=accession_id,
        relpath=file.path
    )


def find_files_in_submission_file_lists(submission: Submission) -> List[File]:

    file_list_fnames = find_file_lists_in_submission(submission)
    file_lists = [flist_from_flist_fname(submission.accno, fname) for fname in file_list_fnames]

    return sum(file_lists, [])


def find_files_in_submission(submission: Submission) -> List[File]:
    """Find all of the files in a submission, both attached directly to
    the submission and as file lists."""
    
    all_files = find_files_in_submission_file_lists(submission)
    
    def descend_and_find_files(section, files_list=[]):
        
        for file in section.files:
            if isinstance(file, List):
                files_list += file
            else:
                files_list.append(file)
            
        for subsection in section.subsections:
            descend_and_find_files(subsection, files_list)
            
    descend_and_find_files(submission.section, all_files)
    
    return all_files