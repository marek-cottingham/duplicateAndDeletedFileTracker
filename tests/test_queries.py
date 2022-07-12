from importlib.resources import files
from . import sql

setupTest_archiveFiles = files(sql).joinpath('setupTest_archiveFiles.sql').read_text()
