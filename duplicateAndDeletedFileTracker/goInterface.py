import ctypes
from pathlib import Path
from typing import List, Tuple
from .main import CursorInterface

def goFilesHash(
    filePaths: List[str]
):
    bytePaths = [path.encode('utf-8') for path in filePaths]
    str_list_type = (ctypes.c_char_p * len(bytePaths))
    str_list = str_list_type(*bytePaths)

    so = ctypes.cdll.LoadLibrary('./duplicateAndDeletedFileTracker/go/_hash.so')
    so.c_hash_list.argtypes = [str_list_type]
    so.c_hash_list.restype = ctypes.c_char_p
    hash_0 = so.c_hash_list(str_list)

    try:
        decode_0 = ctypes.string_at(hash_0).decode('utf-8')
    except UnicodeDecodeError:
        print("Bad return from c_hash_list: ",hash_0)
        raise
    
    # so.free.argtypes = [ctypes.c_void_p]
    # so.free(hash_0)
    return decode_0


def goUpdateFilesHash(
    dbCursor: CursorInterface, 
    rootDir: Path, 
    files_id_path: List[Tuple[int, str]], 
    table_name: str
):  
    paths = [path for _, path in files_id_path]

    hashes = []
    # obtain hashes using go

    for file_path, file_hash in zip(paths, hashes):
        dbCursor.execute(
            f"UPDATE {table_name} SET file_hash = %s WHERE relative_path = %s",
            (file_hash, file_path)
        )
