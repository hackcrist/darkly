package darkly

import "testing"

func TestVersion(t *testing.T) {
	if Version == "" {
		t.Error("Version no debe estar vacía")
	}
}
