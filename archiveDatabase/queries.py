from importlib.resources import files
from . import sql

selectAllCurrentFiles = "SELECT * FROM currentFiles;"
resetCurrentFiles = "DELETE FROM currentFiles;"
resetAllTables = files(sql).joinpath('resetAllTables.sql').read_text()
resetViewAndProcs = files(sql).joinpath('resetViewsAndProcs.sql').read_text()