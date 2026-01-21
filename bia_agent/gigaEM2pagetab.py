import pandas as pd
from .rembi import REMBIContainer

study_mapping = {
    # simple fields (take first non-null value)
    "Study Title": ("study.title", str, True),
    "Study Description": ("study.description", str, True),
    "Study Private Until": ("study.private_until_date", str, True),
    "Study Acknowledgements": ("study.acknowledgements", str, False),

    # list of strings (collect ALL rows)
    "Study Key Words": ("study.keywords[]", str, True),

    # authors (list of objects, one per row)
    "Study Person First Name": ("study.authors[].first_name", str, True),
    "Study Person Last Name": ("study.authors[].last_name", str, True),
    "Study Person E-mail": ("study.authors[].email", str, False),
    "Study Person ORCID": ("study.authors[].orcid", str, False),
    "Study Person Roles": ("study.authors[].role", str, False),

    # nested object inside author
    "Study Person Organisation Name": (
        "study.authors[].affiliation.name", str, True
    ),
    "Study Person Organisation Address": (
        "study.authors[].affiliation.address", str, False
    ),

    # funding (single object + list)
    "Study Funding Statement": (
        "study.funding.funding_statement", str, False
    ),
    "Study Funding Reference Funding Body": (
        "study.funding.grant_references[].funder", str, False
    ),
    "Study Funding Reference Identifier": (
        "study.funding.grant_references[].identifier", str, False
    ),

    # publication (list of objects, one per row)
    "Study Publication Title": ("study.publications[].title", str, False),
    "Study Publication Authors": ("study.publications[].authors", str, False),
    "Study Publication DOI": ("study.publications[].doi", str, False),
    "Study Publication Year": ("study.publications[].year", str, False),
    "Study Publication PMC ID": ("study.publications[].pubmed_id", str, False),

    # links (list of objects, one per row)
    "Study Link URL": ("study.links[].link_url", str, False),
    "Study Link Type": ("study.links[].link_type", str, False),
    "Study Link Description": ("study.links[].link_description", str, False),

}

im_mapping = {
    # biosample simple fields (take first non-null value)
    "biological_entity": ("biosamples.First biosample.biological_entity", str, True),
    # these need to be lists
    "intrinsic_variables": ("biosamples.First biosample.intrinsic_variables", str, False, True),
    "extrinsic_variables": ("biosamples.First biosample.extrinsic_variables", str, False, True),
    "experimental_variables": ("biosamples.First biosample.experimental_variables", str, False, True),

    # nested object inside biosample
    "organism": ("biosamples.First biosample.organism.scientific_name", str, True),

    # specimen simple fields (take first non-null value)
    "sample_preparation": ("specimens.First specimen.sample_preparation", str, True),

    # nested object inside image acquisition
    "imaging_method": ("acquisitions.First acquisition.imaging_method.value", str, True),

    # image acquisition simple fields (take first non-null value)
    "imaging_instrument": ("acquisitions.First acquisition.imaging_instrument", str, True),
    "image_acquisition_parameters": ("acquisitions.First acquisition.image_acquisition_parameters", str, True),
}

ann_mapping = {
    # annotations simple fields (take first non-null value)
    "annotation_overview": ("annotations.Annotations.annotation_overview", str, True),
    "annotation_type": ("annotations.Annotations.annotation_type[]", str, True),
    "annotation_method": ("annotations.Annotations.annotation_method", str, True),
    "annotation_confidence_level": ("annotations.Annotations.annotation_confidence_level", str, False),
    "annotation_criteria": ("annotations.Annotations.annotation_criteria", str, False),
}


def split_path(path: str):
    """
    Splits a path into parts and detects list markers []
    """
    parts = path.split(".")
    parsed = []
    for part in parts:
        if part.endswith("[]"):
            parsed.append((part[:-2], True))
        else:
            parsed.append((part, False))
    return parsed

def set_scalar(output: dict, path_parts, value):
    current = output
    for key, is_list in path_parts[:-1]:
        if key not in current:
            current[key] = {} if not is_list else []
        current = current[key]

    last_key, _ = path_parts[-1]
    current[last_key] = value

def set_list_of_strings(output: dict, path_parts, values):
    current = output
    for key, is_list in path_parts[:-1]:
        current = current.setdefault(key, {})

    list_key, _ = path_parts[-1]
    current[list_key] = values

def set_list_of_objects(output, path_parts, row_index, field_name, value):
    current = output

    # walk until the list
    for key, is_list in path_parts:
        if is_list:
            lst = current.setdefault(key, [])
            # ensure object exists for this row
            while len(lst) <= row_index:
                lst.append({})
            current = lst[row_index]
        else:
            current = current.setdefault(key, {})

    current[field_name] = value

def map_dataframe_to_dict(df: pd.DataFrame, mapping: dict, *, strict=True):
    output = {}

    for csv_col, spec in mapping.items():
        target, dtype, *rest = spec
        required = rest[0] if rest else False
        path_parts = split_path(target)

        # ---- CASE 1: list of strings (e.g. keywords[], annotation_type[]) ----
        if path_parts[-1][1] and not any(is_list for _, is_list in path_parts[:-1]):
            values = (
                df[csv_col]
                .dropna()
                .astype(str)
                .str.strip()
                .tolist()
            )

            if required and not values and strict:
                raise ValueError(f"Missing required values for {csv_col}")

            set_list_of_strings(output, path_parts, values)
            continue

        # ---- CASE 2: scalar (take first non-null) ----
        if not any(is_list for _, is_list in path_parts):
            series = df[csv_col].dropna()
            if series.empty:
                if required and strict:
                    raise ValueError(f"Missing required column/value: {csv_col}")
                continue

            value = dtype(series.iloc[0]) if dtype else series.iloc[0]

            as_list = rest[1] if len(rest) > 1 else False
            if as_list:
                value = [value]

            set_scalar(output, path_parts, value)
            continue

        # ---- CASE 3: list of objects (row-based) ----
        for i, row in df.iterrows():
            value = row.get(csv_col)

            if pd.isna(value):
                continue

            value = dtype(value) if dtype else value

            *prefix, (field, _) = path_parts
            set_list_of_objects(output, prefix, i, field, value)

    return output


def prune_empty(obj):
    if isinstance(obj, dict):
        return {
            k: prune_empty(v)
            for k, v in obj.items()
            if v not in ({}, [], None)
        }
    if isinstance(obj, list):
        return [prune_empty(v) for v in obj if v not in ({}, [])]
    return obj


def build_container(study_path, im_path, ann_path):
    study_df = pd.read_csv(study_path)
    im_df = pd.read_csv(im_path)
    ann_df = pd.read_csv(ann_path)

    data = {}

    # study
    study_df = study_df.set_index(study_df.columns[0]).T
    study_df = study_df.reset_index().rename(columns={"index":"Study Title"})
    study_df = study_df[~study_df.apply(lambda row: row.astype(str).str.startswith("#").any(), axis=1)]  # remove comments

    data.update(map_dataframe_to_dict(study_df, study_mapping))
    data.setdefault("study", {})["rembi_version"] = "1.5"

    # images
    im_df = im_df[~im_df.apply(lambda row: row.astype(str).str.startswith("#").any(), axis=1)]  # remove comments
    im_df.columns = im_df.columns.str.strip() # remove trailing spaces in column names
    
    # we will handle only one study component. If all fields are the same in the csv for a column, we will use that information.
    # otherwise we will just have that info on the file list and have a generic "multiple (see file list)" in/ the study/annotation component
    new_im_df = pd.DataFrame()
    REQUIRED_COLS = {'organism', 'sample_preparation', 'imaging_method', 'imaging_instrument', 'image_acquisition_parameters','annotation_overview','annotation_type','annotation_method','organ_system', 'intrinsic_variables','extrinsic_variables', 'experimental_variables','annotation_confidence_level','annotation_criteria','tissue_location','cell_type'}
    for col in im_df.columns:
        unique_vals = im_df[col].dropna().unique()
        if len(unique_vals) == 1:
            # Keep the column with its single value
            new_im_df[col] = [unique_vals[0]]
        elif len(unique_vals) > 1 and col in REQUIRED_COLS:
                new_im_df[col] = 'multiple (see file list)'
        else:
            new_im_df[col] = [pd.NA]
    
    # we need to create the biological entity from other fields

    row = new_im_df.iloc[0]

    if "multiple (see file list)" in row[["organ_system", "tissue_location", "cell_type"]].values:
        new_im_df.loc[0, "biological_entity"] = "multiple (see file list)"
    else:
        new_im_df.loc[0, "biological_entity"] = ", ".join(
            row[["organ_system", "tissue_location", "cell_type"]].astype(str)
        )
    data.update(map_dataframe_to_dict(new_im_df, im_mapping))
    
    # set default values
    component = (
        data
        .setdefault("biosamples", {})
        .setdefault("First biosample", {})
        .setdefault("organism", {})
    )
    component.setdefault("ncbi_taxon", "")

    component = (
        data
        .setdefault("acquisitions", {})
        .setdefault("First acquisition", {})
        .setdefault("imaging_method", {})
    )
    component.setdefault("ontology_id", "")
    component.setdefault("ontology_name", "")

    # annotations
    ann_df = ann_df[~ann_df.apply(lambda row: row.astype(str).str.startswith("#").any(), axis=1)]  # remove comments
    ann_df.columns = ann_df.columns.str.strip() # remove trailing spaces in column names

    # we will handle only one study component. If all fields are the same in the csv for a column, we will use that information.
    # otherwise we will just have that info on the file list and have a generic "multiple (see file list)" i the study/annotation component
    new_ann_df = pd.DataFrame()
    for col in ann_df.columns:
        unique_vals = ann_df[col].dropna().unique()
        if len(unique_vals) == 1:
            # Keep the column with its single value
            new_ann_df[col] = [unique_vals[0]]
        elif len(unique_vals) > 1 and col in REQUIRED_COLS:
            new_ann_df[col] = 'multiple (see file list)'
        else:
            new_ann_df[col] = [pd.NA]
    
    data.update(map_dataframe_to_dict(new_ann_df, ann_mapping))

    # version - set default values
    component = (
        data
        .setdefault("version", {})
        .setdefault("Annotations", {})
    )
    component.setdefault("version", "v1.0")
    component.setdefault("timestamp", "2025-12-23 13:45:21")

    # study component - set default values (we will only have one for the moment)
    component = (
        data
        .setdefault("study_component", {})
        .setdefault("First study component", {})
    )
    component.setdefault("name", "Imaging data")
    component.setdefault("description", "Raw images used for annotation")
    component.setdefault("rembi_version", "1.5")
    
    # associations - set default values
    component = (
        data
        .setdefault("associations", {})
        .setdefault("First study component", {})
    )
    component.setdefault("biosample_id", "First biosample")
    component.setdefault("specimen_id", "First specimen")
    component.setdefault("acquisition_id", "First acquisition")


    data = prune_empty(data) # remove some cases where there are empty cells

    container = REMBIContainer.parse_obj(data)
    
    return container




'''#delete
im_path = "giga-em/Image_data_many_sc.csv"
ann_path = "giga-em/GIGA-EM_metadata_SynapseNet_Annotation_metadata.csv"
study_path = "giga-em/GIGA-EM_metadata_SynapseNet_Study_metadata.csv"
outdir = "giga-em/test_results"
#test_result = create_file_lists(im_path,ann_path,outdir)
#print(test_result)
dfs = pd.read_csv(study_path)
dfi = pd.read_csv(im_path)
dfa = pd.read_csv(ann_path)

container, study_dict = build_container(dfs,dfi,dfa)

from pprint import pprint

pprint(study_dict, width=100, sort_dicts=False)
pprint(container, width=100, sort_dicts=False)
#print(json.dumps(container.schema(), indent=2))
'''