import contextlib
from datetime import datetime
import hashlib
import os
from pathlib import Path
import sys
from typing import Iterable, List, Tuple
from abc import ABC, abstractmethod

import psycopg2

from archiveDatabase import queries

class CursorInterface(ABC):
    @abstractmethod
    def execute(self, query: str, param: Tuple = None): pass

    @abstractmethod
    def fetchall(self) -> List[Tuple]: pass 

@contextlib.contextmanager
def openConnection(params: dict):
    conn = psycopg2.connect(**params)
    cursor = conn.cursor()
    try:
        yield cursor
    finally:
        cursor.close()
        conn.commit()
        conn.close()

def hashFile(path):
    BUF_SIZE = 65536  # lets read stuff in 64kb chunks!
    sha256 = hashlib.sha256()
    with open(path, 'rb') as file:
        while True:
            data = file.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()

def ingest(rootDir: Path) -> Iterable[dict]:
    for path, subdirs, files in os.walk(rootDir):
        for name in files:

            file_path = Path(path, name)

            properties = {
                'file_path': file_path,
                'relative_path': file_path.relative_to(rootDir),
                'modified': datetime.fromtimestamp( file_path.stat().st_mtime )
            }

            yield properties

def ingestHashAll(rootDir: Path) -> Iterable[dict]:
    for file_properties in ingest(rootDir):
        file_properties['hash'] = hashFile(file_properties['file_path'])
        yield file_properties

def loadCurrentFiles(dbCursor: CursorInterface, rootDir: Path):
    dbCursor.execute(queries.resetCurrentFiles)
    for queryParams in ingest(rootDir):
        dbCursor.execute(
            "INSERT INTO currentFiles (relative_path, modified) VALUES (%s, %s)",
            (str(queryParams['relative_path']),queryParams['modified'])
        )

def updateNewFilesHash(dbCursor: CursorInterface, rootDir: Path):
    dbCursor.execute("SELECT file_id, relative_path FROM newPathFilesWithoutHash")
    files_id_path = dbCursor.fetchall()
    updateFilesHash(dbCursor, rootDir, files_id_path, "currentFiles")

def updateModifiedFilesHash(dbCursor: CursorInterface, rootDir: Path):
    dbCursor.execute("SELECT file_id, relative_path FROM modifiedFiles")
    files_id_path = dbCursor.fetchall()
    updateFilesHash(dbCursor, rootDir, files_id_path, "currentFiles")

def updateFilesHash(
    dbCursor: CursorInterface, 
    rootDir: Path, 
    files_id_path: List[Tuple[int, str]], 
    table_name: str
):
    for file_id, relative_path in files_id_path:
        file_hash = hashFile(Path(rootDir, relative_path))
        dbCursor.execute(
            f"UPDATE {table_name} SET file_hash = %s WHERE file_id = %s",
            (file_hash, file_id)
        )

def prettyPrint(dbCursor: CursorInterface, query: str) -> List[Tuple]:
    print("")
    print('--- ', query, ' ---')
    dbCursor.execute(query)
    result = dbCursor.fetchall()
    for i in result:
        print(i)
    return result

def printDuplicateInstructions():
    print("Enter:")
    print("k### to keep both files")
    print("r### to remove file (LHS)")
    print("kall to keep all in list")
    print("rall to remove all in list (LHS)")
    print("skip to decide later")
    print("exit to stop program")