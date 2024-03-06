from typing import Optional

from .biostudies import Attribute, Submission
from .rembi import REMBIContainer

from .utils import (rembi_study_to_pagetab_submission,
                    biosample_to_pagetab_section,
                    specimen_to_pagetab_section,
                    acquisition_to_pagetab_section,
                    correlation_to_pagetab_section,
                    analysis_to_pagetab_section,
                    study_component_to_pagetab_section,
                    mifa_annotations_to_pagetab_section,
                    ST_MIFA_TEMPLATE_VERSION)

def rembi_mifa_container_to_pagetab(container: REMBIContainer, accession_id: Optional[str], root_path: Optional[str]) -> Submission:
    """Convert a REMBI + MIFA Container object into a PageTab submission."""

    submission = rembi_study_to_pagetab_submission(container.study, template=ST_MIFA_TEMPLATE_VERSION, accession_id=accession_id)

    if root_path:
        submission.attributes.append(Attribute(name="RootPath", value=root_path))

    def rembi_objects_to_pagetab_sections(conversion_func, objects_dict):

        sections = [
            conversion_func(object, object_id)
            for object_id, object in objects_dict.items()
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
    submission.section.subsections += rembi_objects_to_pagetab_sections(
        correlation_to_pagetab_section, container.correlations
    )
    submission.section.subsections += rembi_objects_to_pagetab_sections(
        analysis_to_pagetab_section, container.analysis
    )

    ann_section = [
        mifa_annotations_to_pagetab_section(ann_object, v_object, ann_id)
        for (ann_id, ann_object),(v_id, v_object) in zip(container.annotations.items(),container.version.items())
    ]
    submission.section.subsections += ann_section

    sc_section = [
        study_component_to_pagetab_section(sc_object,a_object)
        for (sc_id, sc_object),(a_id, a_object) in zip(container.study_component.items(),container.associations.items())
    ]

    submission.section.subsections += sc_section

    return submission

def mifa_container_to_pagetab(container: REMBIContainer, accession_id: Optional[str], root_path: Optional[str]) -> Submission:
    """Convert a MIFA Container object into a PageTab submission."""

    submission = rembi_study_to_pagetab_submission(container.study, template=ST_MIFA_TEMPLATE_VERSION, accession_id=accession_id)

    if root_path:
        submission.attributes.append(Attribute(name="RootPath", value=root_path))

    def rembi_objects_to_pagetab_sections(conversion_func, objects_dict):

        sections = [
            conversion_func(object, title=object_id)
            for object_id, object in objects_dict.items()
        ]
        return sections

    ann_section = [
        mifa_annotations_to_pagetab_section(ann_object, v_object, ann_id)
        for (ann_id, ann_object),(v_id, v_object) in zip(container.annotations.items(),container.version.items())
    ]
    submission.section.subsections += ann_section

    return submission