from typing import Optional

from bia_faim_models.schema.bia_faim_models_pydantic import Annotations

from .biostudies import Attribute, Section, Submission
from .rembi import REMBIContainer

from .utils import (append_if_not_none, 
                    rembi_study_to_pagetab_submission,
                    biosample_to_pagetab_section,
                    specimen_to_pagetab_section,
                    acquisition_to_pagetab_section,
                    study_component_to_pagetab_section)

def mifa_annotations_to_pagetab_section(annotations: Annotations, title: str, suffix=1) -> Section:

    annotations_section = Section(
        type="Annotations",
        accno=f"Annotations-{suffix}",
        attributes=[
            Attribute(
                name="Title",
                value=title
            ),
            Attribute(
                name="Annotation overview",
                value=annotations.annotation_overview
            ),
            Attribute(
                name="Annotation method",
                value=annotations.annotation_method
            )
        ])
    
    append_if_not_none(annotations_section.attributes, "Annotation confidence level", annotations.annotation_confidence_level)
    append_if_not_none(annotations_section.attributes, "Annotation criteria", annotations.annotation_criteria)
    append_if_not_none(annotations_section.attributes, "Annotation coverage", annotations.annotation_coverage)
    
    return annotations_section

def rembi_mifa_container_to_pagetab(container: REMBIContainer, accession_id: Optional[str], root_path: Optional[str]) -> Submission:
    """Convert a REMBI + MIFA Container object into a PageTab submission."""

    submission = rembi_study_to_pagetab_submission(container.study, accession_id=accession_id)

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
        mifa_annotations_to_pagetab_section, container.annotations
    )

    sc_section = [
        study_component_to_pagetab_section(sc_object,a_object)
        for (sc_id, sc_object),(a_id, a_object) in zip(container.study_component.items(),container.associations.items())
    ]

    submission.section.subsections += sc_section

    return submission

def mifa_container_to_pagetab(container: REMBIContainer, accession_id: Optional[str], root_path: Optional[str]) -> Submission:
    """Convert a MIFA Container object into a PageTab submission."""

    submission = rembi_study_to_pagetab_submission(container.study, accession_id=accession_id)

    if root_path:
        submission.attributes.append(Attribute(name="RootPath", value=root_path))

    def rembi_objects_to_pagetab_sections(conversion_func, objects_dict):

        sections = [
            conversion_func(object, object_id)
            for object_id, object in objects_dict.items()
        ]
        return sections

    submission.section.subsections += rembi_objects_to_pagetab_sections(
        mifa_annotations_to_pagetab_section, container.annotations
    )

    return submission