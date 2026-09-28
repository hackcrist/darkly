// sys.go: info del sistema, disco, hash de archivos y verificación.
package main

import (
	"crypto/md5"
	"crypto/sha1"
	"crypto/sha256"
	"crypto/sha512"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"hash"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// ---------- sysinfo ----------

func diskInfo() any {
	if runtime.GOOS == "windows" {
		out, err := exec.Command("powershell", "-NoProfile", "-Command",
			"Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free | ConvertTo-Json").Output()
		if err != nil {
			return map[string]string{"nota": "no se pudo leer disco: " + err.Error()}
		}
		var rows any
		if err := json.Unmarshal(out, &rows); err != nil {
			return map[string]string{"nota": "disco sin parsear"}
		}
		return rows
	}
	// Linux/otros: df
	out, err := exec.Command("df", "-h", ".").Output()
	if err != nil {
		return map[string]string{"nota": "no se pudo leer disco: " + err.Error()}
	}
	return map[string]string{"df": strings.TrimSpace(string(out))}
}

func cmdSysInfo(args []string) {
	fs := flag.NewFlagSet("sysinfo", flag.ExitOnError)
	fs.Parse(args)
	host, _ := os.Hostname()
	cwd, _ := os.Getwd()
	emitJSON(map[string]any{
		"sistema":    runtime.GOOS,
		"arquitectura": runtime.GOARCH,
		"nucleos":    runtime.NumCPU(),
		"hostname":   host,
		"go_version": runtime.Version(),
		"cwd":        cwd,
		"disco":      diskInfo(),
	})
}

// ---------- filehash / verify ----------

func openHasher(algo string) (hash.Hash, error) {
	switch strings.ToLower(strings.ReplaceAll(algo, "-", "")) {
	case "md5":
		return md5.New(), nil
	case "sha1":
		return sha1.New(), nil
	case "sha256":
		return sha256.New(), nil
	case "sha512":
		return sha512.New(), nil
	}
	return nil, fmt.Errorf("algoritmo no soportado (md5, sha1, sha256, sha512)")
}

func fileHashCore(path, algo string) (string, int64, error) {
	h, err := openHasher(algo)
	if err != nil {
		return "", 0, err
	}
	f, err := os.Open(path)
	if err != nil {
		return "", 0, err
	}
	defer f.Close()
	var total int64
	buf := make([]byte, 65536)
	for {
		n, err := f.Read(buf)
		if n > 0 {
			total += int64(n)
			if total > 500*1024*1024 {
				return "", 0, fmt.Errorf("archivo muy grande (>500MB)")
			}
			h.Write(buf[:n])
		}
		if err == io.EOF {
			break
		}
		if err != nil {
			return "", 0, err
		}
	}
	abs, _ := filepath.Abs(path)
	_ = abs
	return hex.EncodeToString(h.Sum(nil)), total, nil
}

func cmdFileHash(args []string) {
	fs := flag.NewFlagSet("filehash", flag.ExitOnError)
	algo := fs.String("algo", "sha256", "md5|sha1|sha256|sha512")
	fs.Parse(args)
	if fs.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go filehash --algo sha256 <archivo>")
		os.Exit(2)
	}
	hexsum, size, err := fileHashCore(fs.Arg(0), *algo)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	abs, _ := filepath.Abs(fs.Arg(0))
	emitJSON(map[string]any{"path": abs, "algo": *algo, "hex": hexsum, "bytes": size})
}

func cmdVerify(args []string) {
	fs := flag.NewFlagSet("verify", flag.ExitOnError)
	algo := fs.String("algo", "sha256", "md5|sha1|sha256|sha512")
	fs.Parse(args)
	if fs.NArg() < 2 {
		fmt.Fprintln(os.Stderr, "uso: darkly-go verify --algo sha256 <archivo> <hash-esperado>")
		os.Exit(2)
	}
	hexsum, _, err := fileHashCore(fs.Arg(0), *algo)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	esp := strings.ToLower(strings.Fields(fs.Arg(1))[0])
	ok := strings.ToLower(hexsum) == esp
	out := map[string]any{"calculado": hexsum, "esperado": esp, "coincide": ok}
	if ok {
		out["resultado"] = "COINCIDE - archivo integro"
	} else {
		out["resultado"] = "NO COINCIDE - archivo alterado o corrupto"
	}
	emitJSON(out)
}
