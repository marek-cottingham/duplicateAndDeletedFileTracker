package c_arrstr

import "unsafe"
import "C"

type Ref_ref_string **C.char
type C_int C.int

func From_go_to_c(original []string) unsafe.Pointer {
	cArray := C.malloc(C.size_t(len(original)) * C.size_t(unsafe.Sizeof(uintptr(0))))
	goArray := (*[1<<30 - 1]*C.char)(cArray)
	for idx, substring := range original {
		goArray[idx] = C.CString(substring)
	}
	return cArray
}

func From_c_to_go(path_list **C.char, length C.int) []string {
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
