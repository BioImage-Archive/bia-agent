from typing import Optional

from .biostudies import Attribute, Submission
from .rembi import REMBIContainer, validate_mifa_metadata, validate_rembi_mifa_metadata

from .utils import (rembi_study_to_pagetab_submission,
                    biosample_to_pagetab_section,
                    specimen_to_pagetab_section,
                    acquisition_to_pagetab_section,
                    correlation_to_pagetab_section,
                    analysis_to_pagetab_section,
                    study_component_to_pagetab_section,
                    mifa_annotations_to_pagetab_section,
                    rembi_objects_to_pagetab_sections,
                    ST_MIFA_TEMPLATE_VERSION)

def rembi_mifa_container_to_pagetab(container: REMBIContainer, accession_id: Optional[str], root_path: Optional[str]) -> Submission:
    """Convert a REMBI + MIFA Container object into a PageTab submission."""
    validate_rembi_mifa_metadata(container)

    submission = rembi_study_to_pagetab_submission(container.study, template=ST_MIFA_TEMPLATE_VERSION, accession_id=accession_id)

    if root_path:
        submission.attributes.append(Attribute(name="RootPath", value=root_path))

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
        mifa_annotations_to_pagetab_section(
            annotations=ann_object,
            version=container.version.get(ann_id),
            title=ann_id,
            suffix=n,
        )
        for n, (ann_id, ann_object) in enumerate(container.annotations.items(), start=1)
    ]
    submission.section.subsections += ann_section

    sc_section = [
        study_component_to_pagetab_section(
            study_component=sc_object,
            associations=container.associations[sc_id],
            suffix=n,
        )
        for n, (sc_id, sc_object) in enumerate(container.study_component.items(), start=1)
    ]

    submission.section.subsections += sc_section

    return submission

def mifa_container_to_pagetab(container: REMBIContainer, accession_id: Optional[str], root_path: Optional[str]) -> Submission:
    """Convert a MIFA Container object into a PageTab submission."""
    validate_mifa_metadata(container)

    submission = rembi_study_to_pagetab_submission(container.study, template=ST_MIFA_TEMPLATE_VERSION, accession_id=accession_id)

    if root_path:
        submission.attributes.append(Attribute(name="RootPath", value=root_path))

    ann_section = [
        mifa_annotations_to_pagetab_section(
            annotations=ann_object,
            version=container.version.get(ann_id),
            title=ann_id,
            suffix=n,
        )
        for n, (ann_id, ann_object) in enumerate(container.annotations.items(), start=1)
    ]
    submission.section.subsections += ann_section

    return submission
