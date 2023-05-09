import pathlib
from typing import Dict, List

import fs
import pandas as pd
from pydantic import BaseModel


EXCLUDES = [".DS_Store"]


class SubmissionFile(BaseModel):
    relpath: pathlib.Path
    attrs: Dict = {}
    excluded: Dict = {}

    @property
    def as_bst_file(self):
        bst_dict = {"Files": str(self.relpath)}
        bst_dict.update(self.attrs)

        return bst_dict


class FileCollection(BaseModel):
    files: List[SubmissionFile]

    rootpath: pathlib.Path
    fstype: str

    @classmethod
    def from_fs_path(cls, base_dirpath: pathlib.Path, dirname: pathlib.Path):
        local_fs = fs.open_fs(str(base_dirpath))

        paths_relative_to_base = [
            pathlib.Path(path)
            for path in local_fs.walk.files(str(dirname))
        ]

        files = [
            SubmissionFile(relpath=relpath)
            for relpath in paths_relative_to_base
            if str(relpath.name) not in EXCLUDES
        ]

        return cls(files=files, rootpath=base_dirpath, fstype="local")

    def apply_metadata_extraction_function(self, derivation_function):
        for sfile in self.files:
            included, excluded = derivation_function(sfile)
            sfile.attrs.update(included)
            sfile.excluded.update(excluded)

    def add_metadata_to_all_files(self, key, value):
        for sfile in self.files:
            sfile.attrs[key] = value

    def merge(self, other_file_collection):

        assert self.rootpath == other_file_collection.rootpath
        assert self.fstype == other_file_collection.fstype

        merged_files = self.files.copy() + other_file_collection.files.copy()

        return FileCollection(files=merged_files, rootpath=self.rootpath, fstype=self.fstype)

    def __len__(self):
        return len(self.files)

    def split(self, condition):
    
        first_partition_files = [sfile for sfile in self.files if condition(sfile)]
        second_partition_files = [sfile for sfile in self.files if not condition(sfile)]
    
        first_partition_fc = FileCollection(files=first_partition_files, rootpath=self.rootpath, fstype=self.fstype)
        second_partition_fc = FileCollection(files=second_partition_files, rootpath=self.rootpath, fstype=self.fstype)

        assert len(first_partition_fc) + len(second_partition_fc) == len(self)

        return first_partition_fc, second_partition_fc

    def as_tsv(self, sort_keys):

        as_bst_files = [sfile.as_bst_file for sfile in self.files]

        df = pd.DataFrame(as_bst_files)
        df_sorted = df.sort_values(by=sort_keys)

        return df_sorted.to_csv(index=False, sep="\t")