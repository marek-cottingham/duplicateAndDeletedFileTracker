import ctypes
from typing import List, Type

def goFilesHash(
    filePaths: List[str]
)->List[str]:
    c_array_str, convertedFilePaths = _stringList_to_CstringArray(filePaths)

    lib = ctypes.cdll.LoadLibrary('./duplicateAndDeletedFileTracker/go/_hash.so')

    hashes_pointer = _call_c_hash_list(lib, c_array_str, convertedFilePaths)
    decoded = _decode_hashes_pointer(filePaths, hashes_pointer)
    _free_hashes_pointer(lib, hashes_pointer)

    return decoded

def _free_hashes_pointer(lib, hashes_pointer):
    lib.free_string_array.argtypes = [ctypes.c_void_p]
    lib.free_string_array(hashes_pointer)

def _decode_hashes_pointer(filePaths, hashes_pointer):
    decoded = []
    
    for i in range(len(filePaths)):
        try:
            decoded.append(ctypes.string_at(hashes_pointer[i]).decode('utf-8'))
        except UnicodeDecodeError:
            print(f"Bad return from c_hash_list[{i}]: {hashes_pointer[i]}")
            raise
    return decoded

def _call_c_hash_list(
    lib: ctypes.CDLL,
    c_array_str: Type,
    convertedFilePaths: ctypes.Array[ctypes.c_char_p]
) -> ctypes.POINTER(ctypes.c_void_p):

    lib.c_hash_list.argtypes = [c_array_str, ctypes.c_int]
    lib.c_hash_list.restype = ctypes.POINTER(ctypes.c_void_p)
    hashes_pointer = lib.c_hash_list(convertedFilePaths, ctypes.c_int(len(convertedFilePaths)))
    return hashes_pointer

def _stringList_to_CstringArray(list_strings):
    list_bytes = [s.encode('utf-8') for s in list_strings]
    instance_type = (ctypes.c_char_p * len(list_bytes))
    array_cStrings = instance_type(*list_bytes)
    return instance_type, array_cStrings