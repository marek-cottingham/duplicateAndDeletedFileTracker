package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"unsafe"

	"marek/duplicateAndDeletedFileTracker/duplicateAndDeletedFileTracker/go/c_arrstr"
	"marek/duplicateAndDeletedFileTracker/duplicateAndDeletedFileTracker/go/hash"
)

//export c_hash_list
func c_hash_list(path_list **C.char, length int) **C.char {
	// In order to pass path_list to the package c_arrstr,
	// we need to convert it to use the **C.char type from the package c_arrstr
	// which is exported under the name PP_char.
	retyped_path_list := c_arrstr.PP_char(unsafe.Pointer(path_list))

	slice := c_arrstr.From_c_to_go(retyped_path_list, length)
	hashes := hash.Hash_list(slice)
	cArray := c_arrstr.From_go_to_c(hashes)
	return (**C.char)(cArray)
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
