from __future__ import annotations

import contextlib
import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterable, List, Tuple

import psycopg2

from . import queries
from .goInterface import goHashFiles


class CursorInterface(ABC):
    @abstractmethod
    def execute(self, query: str, param: Tuple = None): pass

    @abstractmethod
    def fetchall(self) -> List[Tuple]: pass

class ExtendedCursorInterface(CursorInterface):
    @abstractmethod
    def getResult(self, query: str, param: Tuple = None) -> List[Tuple]: pass

@dataclass
class CursorWrapper(ExtendedCursorInterface):
    cursor: CursorInterface

    def execute(self, query: str, param: Tuple = None):
        return self.cursor.execute(query, param)

    def fetchall(self) -> List[Tuple]:
        return self.cursor.fetchall()

    def getResult(self, query: str, param: Tuple = None) -> List[Tuple]:
        self.execute(query, param)
        return self.fetchall()

class openConnection:
    def __init__(self, db_params: str):
        self.db_params = db_params
        self.connection = None
        self.cursor = None
        self.cursor_wrapper = None

    def __enter__(self):
        self.connection = psycopg2.connect(**self.db_params)
        self.cursor = self.connection.cursor()
        self.cursor_wrapper = CursorWrapper(self.cursor)
        return self.cursor_wrapper

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        self.connection.close()

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
    goUpdateFilesHash(dbCursor, rootDir, files_id_path, "currentFiles")

def updateModifiedFilesHash(dbCursor: CursorInterface, rootDir: Path):
    dbCursor.execute("SELECT file_id, relative_path FROM modifiedFiles")
    files_id_path = dbCursor.fetchall()
    goUpdateFilesHash(dbCursor, rootDir, files_id_path, "currentFiles")

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

def goUpdateFilesHash(
    dbCursor: CursorInterface, 
    rootDir: Path, 
    files_id_path: List[Tuple[int, str]], 
    table_name: str
):  
    relPaths = [path for _, path in files_id_path]
    absPaths = [str(Path(rootDir,path)) for _, path in files_id_path]
    hashes = goHashFiles(absPaths)

    for file_path, file_hash in zip(relPaths, hashes):
        if file_hash[:5] != "Error":
            dbCursor.execute(
                f"UPDATE {table_name} SET file_hash = %s WHERE relative_path = %s",
                (file_hash, file_path)
            )
        else:
            print(file_hash)


def prettyPrint(
    dbCursor: ExtendedCursorInterface, 
    query: str, 
    result: List[Tuple] | None = None
) -> List[Tuple]:

    print("")
    print('--- ', query, ' ---')
    if result is None:
        result = dbCursor.getResult(query)
    for i in result:
        print(i)
    return result

def printDuplicateInstructions():
    print("Enter:")
    print("k### to keep both files")
    print("r### to remove duplicate file")
    print("kall to keep all in list")
    print("rall to remove all in list")
    print("skip to decide later")
    print("exit to stop program")

def promptUserDuplicates(
    cursor: ExtendedCursorInterface, 
    query: str, 
    callbacks: dict[str,Callable]
):
    """
    callbacks expected key-value pairs:
        "kall": callable(),
        "k###": callable(file_id: int),
        "rall": callable(),
        "r###": callable(file_id: int),
    """
    while(True):
        queryResult = cursor.getResult(query)
        emptyQuery = len(queryResult) == 0
        if emptyQuery: break

        prettyPrint(cursor, query, queryResult)
        printDuplicateInstructions()

        command = input(">>>")

        if (command == "exit"): exit()
        if (command == "skip"): break
        if   (command == "kall"): callbacks["kall"]()
        elif (command[0] == "k"): callbacks["k###"](parseIdFromCommand(command))
        if   (command == "rall"): callbacks["rall"]()
        elif (command[0] == 'r'): callbacks["r###"](parseIdFromCommand(command))

def parseIdFromCommand(command):
    input_id = None
    try:
        input_id = int(command[1:])
    except ValueError:
        print("~~~ Input ID invalid ~~~")
    return input_id

def getDuplicateManagementCallbacks(cursor: ExtendedCursorInterface, duplicateView: str, rootPath: Path):
    if duplicateView == "duplicateFiles":
        k_all_proc = "keepAllDuplicates"
        k_id_proc = "keepDuplicate"
        r_all_proc = "removeAllDuplicates"
        r_id_proc = "removeDuplicate"
            
    if duplicateView == "duplicatePreviouslyDeletedFiles":
        k_all_proc = "keepAllDuplicatesDeleted"
        k_id_proc = "keepDuplicateDeleted"
        r_all_proc = "removeAllDuplicatesDeleted"
        r_id_proc = "removeDuplicate"

    def rall():
        for (relative_path,) in cursor.getResult(f"SELECT relative_path FROM {duplicateView}"):
            Path(rootPath, relative_path).unlink()
        cursor.execute(f"call {r_all_proc}()")

    def r_id(id):
        if id is None: return
        for (relative_path,) in cursor.getResult(
                f"SELECT relative_path FROM {duplicateView} WHERE file_id = {id}"
            ):
            Path(rootPath, relative_path).unlink()
            cursor.execute(f"call {r_id_proc}(%s)",(id,))

    def k_id(id):
        if id is None: return
        cursor.execute(f"call {k_id_proc}(%s)",(id,))

    callbacks = {
            "kall": lambda   : cursor.execute(f"call {k_all_proc}()"),
            "k###": k_id,
            "rall": rall,
            "r###": r_id
        }
    
    return callbacks
