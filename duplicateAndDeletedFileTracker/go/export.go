package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"unsafe"

	"marek/duplicateAndDeletedFileTracker/duplicateAndDeletedFileTracker/go/hash"
)

//export c_hash_list
func c_hash_list(path_list **C.char, length C.int) **C.char {
	slice := arrayString_from_c_to_go(path_list, length)
	hashes := hash.Hash_list(slice)
	cArray := arrayString_from_go_to_c(hashes)
	return (**C.char)(cArray)
}

func arrayString_from_go_to_c(original []string) unsafe.Pointer {
	cArray := C.malloc(C.size_t(len(original)) * C.size_t(unsafe.Sizeof(uintptr(0))))
	goArray := (*[1<<30 - 1]*C.char)(cArray)
	for idx, substring := range original {
		goArray[idx] = C.CString(substring)
	}
	return cArray
}

func arrayString_from_c_to_go(path_list **C.char, length C.int) []string {
	var slice []string
	for _, s := range unsafe.Slice(path_list, length) {
		if s == nil {
			break
		}
		x := C.GoString(s)
		slice = append(slice, x)
	}
	return slice
}

//export free_string_array
func free_string_array(p **C.char) {
	C.free(unsafe.Pointer(p))
}

//export c_hash_file
func c_hash_file(path *C.char) *C.char {
	hash, _ := hash.Hash_file(C.GoString(path))
	return C.CString(hash)
}

//export free_string
func free_string(p *C.char) {
	C.free(unsafe.Pointer(p))
}

func main() {}

// export using: go build -buildmode=c-shared -o _hash.so
