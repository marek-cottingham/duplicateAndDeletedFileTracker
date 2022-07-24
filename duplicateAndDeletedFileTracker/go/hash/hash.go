package hash

import (
	"crypto/sha256"
	"fmt"
	"io"
	"os"

	"golang.org/x/sync/errgroup"
)

func Hash_file(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	sha256 := sha256.New()
	if _, err := io.Copy(sha256, file); err != nil {
		return "", err
	}

	return fmt.Sprintf("%x", sha256.Sum(nil)), nil
}

func Hash_list(filePaths []string) []string {
	hashes := make([]string, len(filePaths))
	var g errgroup.Group
	for i, filePath := range filePaths {
		i, filePath := i, filePath
		hashes[i] = "Error: Not populated"
		g.Go(func() error {
			hash, err := Hash_file(filePath)
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
