import tests
from pathlib import Path
from importlib.resources import files, as_file

class config:
    rootPath: Path = None
    fileStructurePath: Path = None
    connect: dict = {
        'dbname': 'duplicateAndDeletedFileTrackerTest',
        'user': 'postgres',
        'password': 'test'
    }

with as_file(files(tests).joinpath('temp_testFileStructure')) as path:
    config.rootPath = path

with as_file(files(tests).joinpath('testFileStructure')) as path:
    config.fileStructurePath = path