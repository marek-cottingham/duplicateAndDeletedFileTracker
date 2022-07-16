
from pathlib import Path

class config:
    rootPath: Path = Path('\\folder\\where\\archive\\to\\track\\is\\located')
    connect: dict = {
        'dbname': 'NAME',
        'user': 'USERNAME',
        'password': 'PASSWORD',
        'host': 'localhost',
        'port': 5432,
    }
