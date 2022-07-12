from importlib.resources import files
from . import sql

selectAllCurrentFiles = "SELECT * FROM currentFiles;"
resetCurrentFiles = "DELETE FROM currentFiles;"
resetAll = files(sql).joinpath('resetAll.sql').read_text()
