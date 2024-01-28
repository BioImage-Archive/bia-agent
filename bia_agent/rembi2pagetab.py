from typing import Optional

from .biostudies import Attribute, Submission
from .rembi import REMBIContainer
from .utils import (rembi_study_to_pagetab_submission,
                    biosample_to_pagetab_section,
                    specimen_to_pagetab_section,
                    acquisition_to_pagetab_section)


def rembi_container_to_pagetab(container: REMBIContainer, accession_id: Optional[str], root_path: Optional[str]) -> Submission:
    """Convert a REMBI Container object into a PageTab submission."""

    submission = rembi_study_to_pagetab_submission(container.study, accession_id=accession_id)

    if root_path:
        submission.attributes.append(Attribute(name="RootPath", value=root_path))

    def rembi_objects_to_pagetab_sections(conversion_func, objects_dict):
        sections = [
            conversion_func(object, title=object_id, suffix=n)
            for n, (object_id, object) in enumerate(objects_dict.items(), start=1)
        ]

        return sections

    submission.section.subsections += rembi_objects_to_pagetab_sections(
        biosample_to_pagetab_section, container.biosamples
    )
    submission.section.subsections += rembi_objects_to_pagetab_sections(
        specimen_to_pagetab_section, container.specimens
    )
    submission.section.subsections += rembi_objects_to_pagetab_sections(
        acquisition_to_pagetab_section, container.acquisitions
    )

    return submission