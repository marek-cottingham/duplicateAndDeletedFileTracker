import tests
from pathlib import Path
from importlib.resources import files, as_file

class config:
    rootPath: Path = None
    connect: dict = {
        'dbname': 'photoArchiveTest',
        'user': 'postgres',
        'password': 'test'
    }

with as_file(files(tests).joinpath('testFileStructure')) as path:
    config.rootPath = path