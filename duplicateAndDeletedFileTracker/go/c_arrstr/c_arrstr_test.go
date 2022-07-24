package c_arrstr_test

import (
	"marek/duplicateAndDeletedFileTracker/duplicateAndDeletedFileTracker/go/c_arrstr"
	"strings"
	"testing"
)

func FuzzArrStr(f *testing.F) {
	f.Add("a", "b4i4i", "Error: misc")
	f.Add("b", "b4i4iaeddedaddadeddad", "")
	f.Add("0", "0\x00", "\x00")

	f.Fuzz(func(t *testing.T, a string, b string, c string) {

		testArr := []string{a, b, c}
		cArray := c_arrstr.From_go_to_c(testArr)
		retyped_cArray := c_arrstr.PP_char((cArray))
		goArray := c_arrstr.From_c_to_go(retyped_cArray, len(testArr))

		_compare_FuzzArrStr(goArray, testArr, t)
	})

}

func _compare_FuzzArrStr(goArray []string, testArr []string, t *testing.T) {
	if len(goArray) != len(testArr) {
		t.Errorf("Expected output length %d, got %d", len(testArr), len(goArray))
	}
	for idx, substring := range goArray {
		values_not_equal := substring != testArr[idx]
		// limitation imposed by C.CString and/or C.GoString
		no_null_char_in_input := !strings.Contains(testArr[idx], "\x00")
		if values_not_equal && no_null_char_in_input {
			t.Errorf("Expected output %x at index %v, got %x", testArr[idx], idx, substring)
		}
	}
}
