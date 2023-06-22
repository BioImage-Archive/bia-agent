import os
import logging
import pathlib

import fs
import fs.ftpfs
from dotenv import load_dotenv

logger = logging.getLogger("bia-agent")


from .files import FileCollection


def copy_single_file(bia_submission, local_fpath):

    load_dotenv()

    biostudies_secret_dir = os.getenv("BIOSTUDIES_SECRET_DIR")

    logger.info(f"Copying {local_fpath}")

    ftp_fs = fs.ftpfs.FTPFS('ftp-private.ebi.ac.uk', user='bsftp', passwd='bsftp1')

    base_remote_prefix = pathlib.Path(biostudies_secret_dir) 
    submission_basepath = base_remote_prefix / bia_submission.name
    files_dirpath = submission_basepath/"files"

    sub_fs = fs.open_fs(".")

    remote_fpath = files_dirpath/local_fpath.name

    fs.copy.copy_file(sub_fs, str(local_fpath), ftp_fs, str(remote_fpath))


def copy_all(submission_id: str, fc: FileCollection):
    """Copy all of the files in a File Collection (read from a JSON file) to
    BioStudies user space, using FTP."""

    load_dotenv()

    biostudies_secret_dir = os.getenv("BIOSTUDIES_SECRET_DIR")

    ftp_fs = fs.ftpfs.FTPFS('ftp-private.ebi.ac.uk', user='bsftp', passwd='bsftp1')

    base_remote_prefix = pathlib.Path(biostudies_secret_dir) 
    submission_basepath = base_remote_prefix / submission_id

    files_dirpath = submission_basepath/"files"

    ftp_fs.makedir(str(submission_basepath), recreate=True)
    ftp_fs.makedir(str(files_dirpath), recreate=True)

    sub_fs = fs.open_fs(str(fc.rootpath))

    sfiles = fc.files
    n_files = len(sfiles)

    for n, sfile in enumerate(sfiles, start=1):
        relpath_dir_components = sfile.relpath.parent.parts
        current_remote_dir = files_dirpath
        for component in relpath_dir_components:
            current_remote_dir = current_remote_dir / component
            ftp_fs.makedir(str(current_remote_dir), recreate=True)
            
        local_fpath = sfile.relpath
        remote_fpath = files_dirpath / sfile.relpath  
        
        if fs.copy.copy_file_if(sub_fs, str(local_fpath), ftp_fs, str(remote_fpath), condition="newer"):
            logger.info(f"[{n}/{n_files}] Copied {local_fpath} to {remote_fpath}")
        else:
            logger.info(f"[{n}/{n_files}] {local_fpath}, present at remote end")


def verify(submission_id: str, fc: FileCollection):
    """Check that all of the files in a given File Collection are present in
    BioStudies user space, and that their file sizes match."""

    load_dotenv()

    biostudies_secret_dir = os.getenv("BIOSTUDIES_SECRET_DIR")

    ftp_fs = fs.ftpfs.FTPFS('ftp-private.ebi.ac.uk', user='bsftp', passwd='bsftp1')

    base_remote_prefix = pathlib.Path(biostudies_secret_dir) 
    submission_basepath = base_remote_prefix / submission_id
    files_dirpath = submission_basepath/"files"

    sub_fs = fs.open_fs(str(fc.rootpath))

    n_files = len(fc)
    for n, sfile in enumerate(fc.files, start=1):
        info_local = sub_fs.getinfo(str(sfile.relpath), namespaces=['details'])
        info_remote = ftp_fs.getinfo(str(files_dirpath / sfile.relpath), namespaces=['details'])

        logger.info(f"[{n}/{n_files}] Checking {sfile.relpath}")
        if not info_local.size == info_remote.size:
            logger.info(f"Error, re-copying {sfile.relpath}")
            fs.copy.copy_file(sub_fs, str(sfile.relpath), ftp_fs, str(files_dirpath / sfile.relpath))