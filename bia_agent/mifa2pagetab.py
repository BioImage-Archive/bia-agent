from typing import Optional

from bia_faim_models.schema.bia_faim_models_pydantic import Annotations
from bia_rembi_models.study import Study
from bia_rembi_models.sample import Biosample
from bia_rembi_models.specimen import Specimen
from bia_rembi_models.acquisition import ImageAcquisition
from bia_rembi_models.analysis import ImageAnalysis
from bia_rembi_models.study_component import StudyComponent
from bia_rembi_models.correlation import ImageCorrelation

from .biostudies import Attribute, Section, Submission, Link
from .rembi import REMBIContainer, REMBIAssociation

VERSION = "1.0.0"

def append_if_not_none(attr_list, name, value):
    if value:
        attr_list.append(Attribute(name=name, value=value))

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

def generate_org_map(rembi_study):
    organisations = set(author.affiliation for author in rembi_study.authors)
    org_map = {
        org: f"o{n}"
        for n, org in enumerate(organisations, start=1)
    }
    
    return org_map


def organisation_and_label_to_pagetab_section(org, org_label):
    org_attributes = []
    org_attributes.append(Attribute(name="Name", value=org.name))
    if hasattr(org, 'address'):
        org_attributes.append(Attribute(name="Address", value=org.address))
    if hasattr(org, 'url'):
        org_attributes.append(Attribute(name="RORID", value=org.url))

    org_section = Section(
        accno=org_label,
        type="organization",
        attributes=org_attributes
    )
    
    return org_section


def rembi_author_to_pagetab_section(author, org_map):

    full_name = f"{author.first_name} {author.last_name}"

    name_attr = Attribute(name="Name", value=full_name)
    org_attr = Attribute(name="affiliation", value=org_map[author.affiliation], reference=True)

    author_attributes = [name_attr]

    # email_attr = Attribute(name="Email", value=author.email)
    # role_attr = Attribute(name="Role", value=author.role)
    # orcid_attr = Attribute(name="ORCID", value=author.orcid)

    append_if_not_none(author_attributes, "Email", author.email)
    append_if_not_none(author_attributes, "Role", author.role)
    append_if_not_none(author_attributes, "ORCID", author.orcid)

    author_attributes.append(org_attr)

    author_section = Section(
        type="author",
        attributes=author_attributes
    )  # type: ignore
    
    return author_section


def rembi_publication_to_pagetab_section(pub) -> Section:

    pub_attributes = []
    append_if_not_none(pub_attributes, "Title", pub.title)
    append_if_not_none(pub_attributes, "Year", pub.year)
    append_if_not_none(pub_attributes, "Authors", pub.authors)
    append_if_not_none(pub_attributes, "DOI", pub.doi)
    append_if_not_none(pub_attributes, "PMC ID", pub.pubmed_id)

    pub_section = Section(
        accno=None,
        type="Publication",
        attributes=pub_attributes
    )

    return pub_section


def rembi_study_to_pagetab_submission(rembi_study: Study, accession_id: Optional[str], collection: str = "BioImages") -> Submission:

    org_map = generate_org_map(rembi_study)

    org_sections = [
        organisation_and_label_to_pagetab_section(org, org_label)
        for org, org_label in org_map.items()
    ]

    author_sections = [
        rembi_author_to_pagetab_section(author, org_map)
        for author in rembi_study.authors
    ]

    publication_sections = [
        rembi_publication_to_pagetab_section(pub)
        for pub in rembi_study.publications
    ]

    subsections = author_sections + org_sections + publication_sections

    study_attributes = [
        Attribute(name="Description", value=rembi_study.description),
    ]

    if rembi_study.license:
        license_attr = Attribute(name="License", value=rembi_study.license.license_name)
        study_attributes.append(license_attr)

    keyword_attributes = [
        Attribute(name="Keyword", value=keyword)
        for keyword in rembi_study.keywords
    ]
    study_attributes += keyword_attributes

    study_links = []
    for link in rembi_study.links:
        link_attrs = []
        if link.link_type:
            link_attrs.append(Attribute(name="Type", value=link.link_type))
        if link.link_description:
            link_attrs.append(Attribute(name="Description", value=link.link_description))
        study_links.append(Link(url=link.link_url, attributes=link_attrs))
        

    if rembi_study.acknowledgements:
        ack_attr = Attribute(name="Acknowledgements", value=rembi_study.acknowledgements)
        study_attributes.append(ack_attr)

    if rembi_study.funding:
        if rembi_study.funding.funding_statement:
            funding_attr = Attribute(name="Funding statement", value=rembi_study.funding.funding_statement)
            study_attributes.append(funding_attr)

        funding_sections=[]
        for grant_reference in rembi_study.funding.grant_references:
            s = Section(
                type="Funding",
                accno=None,
                attributes=[
                    Attribute(name="Agency", value=grant_reference.funder),
                    Attribute(name="grant_id", value=grant_reference.identifier)
                ]
            )
            funding_sections.append(s)

        subsections += funding_sections

    study_section = Section(
        type="Study",
        attributes=study_attributes,
        subsections=subsections,
        links = study_links
    )  # type: ignore


    global VERSION
    submission = Submission(
        accno=accession_id,
        attributes=[
            Attribute(name="Title", value=rembi_study.title),
            Attribute(name="ReleaseDate", value=rembi_study.private_until_date.strftime("%Y-%m-%d")),
            Attribute(name="AttachTo", value=collection),
            Attribute(name="REMBI_PageTab Conversion Script Version", value=VERSION)
        ],
        section=study_section,
    )
    
    return submission


def biosample_to_pagetab_section(biosample: Biosample, title: str, suffix=1) -> Section:

    organism_section = Section(
        type="Organism",
        accno=f"Organism-{suffix}",
        attributes=[
            Attribute(
                name="Scientific name",
                value=biosample.organism.scientific_name
            ),
            Attribute(
                name="Common name",
                value=biosample.organism.common_name
            ),
            Attribute(
                name="NCBI taxon ID",
                value=biosample.organism.ncbi_taxon
            ),
        ])
    
    biosample_section_attributes = [
        Attribute(
            name="Title",
            value=title
        )
    ]

    biosample_section_attributes.append(
        Attribute(
            name="Biological entity",
            value=biosample.biological_entity
        )
    )

    if biosample.description:
        biosample_section_attributes += [
            Attribute(
                name="Description",
                value=biosample.description
            )
        ]

    for intrinsic_variable in biosample.intrinsic_variables:
        biosample_section_attributes.append(
            Attribute(
                name="Intrinsic variable",
                value=intrinsic_variable
            )
        )

    for extrinsic_variable in biosample.extrinsic_variables:
        biosample_section_attributes.append(
            Attribute(
                name="Extrinsic variable",
                value=extrinsic_variable
            )
        )

    for experimental_variable in biosample.experimental_variables:
        biosample_section_attributes.append(
            Attribute(
                name="Experimental variable",
                value=experimental_variable
            )
        )

    biosample_section = Section(
        type="Biosample",
        accno=f"Biosample-{suffix}",
        subsections=[organism_section],
        attributes=biosample_section_attributes
    )
    
    return biosample_section


def analysis_to_pagetab_section(analysis: ImageAnalysis, suffix=1) -> Section:

    analysis_section = Section(
        type="Image Analysis",
        accno=f"Image-Analysis-{suffix}",
        attributes=[
            Attribute(
                name="Image Analysis Overview",
                value=analysis.analysis_overview
            )
        ]
    )

    return analysis_section


def specimen_to_pagetab_section(specimen: Specimen, title: str, suffix=1) -> Section:

    specimen_section = Section(
        type="Specimen",
        accno=f"Specimen-{suffix}",
        attributes=[
            Attribute(
                name="Title",
                value=title
            ),
            Attribute(
                name="Sample Preparation Protocol",
                value=specimen.sample_preparation
            )
        ]
    )

    if specimen.growth_protocol:
        specimen_section.attributes.append(
            Attribute(
                name="Growth Protocol",
                value=specimen.growth_protocol
            )
        )

    return specimen_section


def acquisition_to_pagetab_section(acquisition: ImageAcquisition, title: str, suffix=1) -> ImageAcquisition:

    ontology_entry = acquisition.imaging_method
    method_section = Section(
        type="Imaging Method",
        accno=f"Imaging Method-{suffix}",
        attributes=[
            Attribute(
                name="Ontology Value",
                value=ontology_entry.value
            ),
            Attribute(
                name="Ontology Name",
                value=ontology_entry.ontology_name
            ),
            Attribute(
                name="Ontology Term ID",
                value=ontology_entry.ontology_id
            )
        ]
    )

    acquisition_section = Section(
        type="Image Acquisition",
        accno=f"Image Acquisition-{suffix}",
        attributes=[
            Attribute(
                name="Title",
                value=title
            ),
            Attribute(
                name="Imaging Instrument",
                value=acquisition.imaging_instrument
            ),
            Attribute(
                name="Image Acquisition Parameters",
                value=acquisition.image_acquisition_parameters
            )
        ],
        subsections=[method_section]
    )

    return acquisition_section

def correlation_to_pagetab_section(correlation: ImageCorrelation, suffix=1) -> Section:
    correlation_section = Section(
        type="Image Correlation",
        accno=f"Image Correlation-{suffix}",
        attributes=[
            Attribute(
                name="Spatial and temporal alignment",
                value=correlation.spatial_and_temporal_alignment
            ),
            Attribute(
                name="Fiducials used",
                value=correlation.fiducials_used
            ),
            Attribute(
                name="Transformation matrix",
                value=correlation.transformation_matrix
            )
        ]
    )

    return correlation_section

def rembi_association_to_pagetab_section(associations: REMBIAssociation) -> Section:

    association_section = Section(
        type="Associations",
        attributes=[
            Attribute(name="Biosample", value=associations.biosample_id),
            Attribute(name="Specimen", value=associations.specimen_id),
            Attribute(name="Image acquisition", value=associations.acquisition_id)
        ]
    )

    return association_section

def study_component_to_pagetab_section(study_component: StudyComponent, associations: REMBIAssociation, suffix=1) -> Section:

    study_component_section = Section(
        type="Study Component",
        accno=f"Study Component-{suffix}",
        attributes=[
            Attribute(
                name="Name",
                value=study_component.name
            ),
            Attribute(
                name="Description",
                value=study_component.description
            ),
        ],
        subsections=[rembi_association_to_pagetab_section(associations)]
    )
    
    return study_component_section

def create_study_component(name: str, description: str, association: REMBIAssociation, file_list_fname: str, suffix=1):

    study_component_section = Section(
        type="Study Component",
        accno=f"Study Component-{suffix}",
        attributes=[
            Attribute(
                name="Name",
                value=name
            ),
            Attribute(
                name="Description",
                value=description
            ),
            Attribute(
                name="File List",
                value=file_list_fname
            )
        ],
        subsections=[rembi_association_to_pagetab_section(association)]
    )
    
    return study_component_section


def create_annotations_section(name: str, description: str, file_list_fname: str, suffix=1):

    annotations = Section(
        type="Annotations",
        accno=f"Annotations-{suffix}",
        attributes=[
            Attribute(
                name="Title",
                value=name
            ),
            Attribute(
                name="Annotation overview",
                value=description
            ),
            Attribute(
                name="File List",
                value=file_list_fname
            )
        ]
    )

    return annotations

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