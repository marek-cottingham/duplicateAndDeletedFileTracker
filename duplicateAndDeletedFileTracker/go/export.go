package main

/*
#include <stdlib.h>
*/
import "C"
import (
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"strings"
	"unsafe"

	"golang.org/x/sync/errgroup"
)

func hash_file(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	sha256 := sha256.New()
	if _, err := io.Copy(sha256, file); err != nil {
		return "", err
	}

	return "hash", nil
	//return string(sha256.Sum(nil)), nil
}

func hash_list(filePaths []string) []string {
	hashes := make([]string, len(filePaths))
	var g errgroup.Group
	for i, filePath := range filePaths {
		i, filePath := i, filePath
		hashes[i] = "Error: Not populated"
		g.Go(func() error {
			hash, err := hash_file(filePath)
			if err != nil {
				hashes[i] = "Error: " + err.Error() + " Path: " + filePath
			}
			if err == nil {
				hashes[i] = hash
			}
			return nil
		})
	}
	g.Wait()
	return hashes
}

//export c_hash_list
func c_hash_list(path_list **C.char) *C.char {
	var slice []string
	for _, s := range unsafe.Slice(path_list, 1<<22) {
		if s == nil {
			break
		}
		slice = append(slice, C.GoString(s))
	}
	hashes := hash_list(slice)
	return C.CString(strings.Join(hashes, "\n"))
}

//export c_hash_file
func c_hash_file(path *C.char) *C.char {
	hash, _ := hash_file(C.GoString(path))
	return C.CString(hash)
}

//export free_string
func free_string(p *C.char) {
	fmt.Println(C.GoString(p))
	C.free(unsafe.Pointer(p))
}

//export free_string_list
func free_string_list(p **C.char) {
	C.free(unsafe.Pointer(p))
}

func main() {}

// export using: go build -buildmode=c-shared -o _hash.so
