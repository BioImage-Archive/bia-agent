import os
import logging
import pathlib

import fs
import fs.ftpfs
from dotenv import load_dotenv

logger = logging.getLogger("bia-agent")


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