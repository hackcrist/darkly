// menu.go: menú interactivo Darkly-Go en español con neón ANSI.
package main

import (
	"bufio"
	"fmt"
	"os"
	"sort"
	"strings"
)

const (
	nc = "\033[38;2;0;255;234m"
	np = "\033[38;2;255;0;255m"
	ng = "\033[38;2;57;255;20m"
	ny = "\033[38;2;255;255;0m"
	nv = "\033[38;2;176;38;255m"
	no = "\033[38;2;255;110;0m"
	dim = "\033[2m"
	bold = "\033[1m"
	end = "\033[0m"
)

var reader = bufio.NewReader(os.Stdin)

func ask(prompt string) string {
	fmt.Printf(" %s%s>%s %s:%s ", nc, bold, end, prompt, end)
	s, _ := reader.ReadString('\n')
	return strings.TrimSpace(s)
}

func bannerGo() {
	fmt.Println()
	fmt.Println(nc + bold + "  ____             _    _" + end)
	fmt.Println(nc + bold + " |  _ \\  __ _ _ __| | _| |_   _" + end)
	fmt.Println(ng + bold + " | | | |/ _` | '__| |/ / | | | |" + end)
	fmt.Println(ny + bold + " | |_| | (_| | |  |   <| | |_| |" + end)
	fmt.Println(np + bold + " |____/ \\__,_|_|  |_|\\_\\\\_|\\__, |" + end)
	fmt.Println(nv + bold + "                          |___/" + end)
	fmt.Println("  Herramientas en Go " + ny + bold + "(educativo)" + end + "  " + ny + bold + "v2.1.0" + end)
	fmt.Println("  Solo fines educativos. Úsalo con responsabilidad y autorización.\n")
}

func showMenu(opts [][2]string) {
	fmt.Printf(" %s%s+--%s%s\n", nv, bold, strings.Repeat("-", 50)+"+", end)
	for _, o := range opts {
		fmt.Printf(" %s|%s  %s%s[%s]%s > %s\n", dim+nv, end, nc, bold, o[0], end, o[1])
	}
	fmt.Printf(" %s%s+%s%s\n", nv, bold, strings.Repeat("-", 52)+"+", end)
}

func printMap(m map[string]any) {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		fmt.Printf("   %s%-15s%s : %v\n", nc, k, end, m[k])
	}
}

func pauseGo() {
	fmt.Print("  Pulsa Enter para continuar...")
	reader.ReadString('\n')
}

func confirmGo() bool {
	fmt.Println("  Solo analiza equipos propios o con autorización escrita.")
	a := strings.ToLower(ask("¿Confirmas que tienes autorización? [s/N]"))
	return a == "s" || a == "si" || a == "y" || a == "yes"
}

func runMenu() {
	for {
		bannerGo()
		fmt.Printf(" %s%s+-- MENU PRINCIPAL --%s%s\n", np, bold, strings.Repeat("-", 30)+"+", end)
		showMenu([][2]string{{"1", "Redes"}, {"2", "Seguridad"}, {"3", "IP / Info"}, {"4", "Sistema"}, {"5", "Usuarios"}, {"0", "Salir"}})
		switch ask("Elige") {
		case "0":
			fmt.Println("\n  Adiós.\n")
			return
		case "1":
			menuRedes()
		case "2":
			menuSeg()
		case "3":
			menuIP()
		case "4":
			menuSys()
		case "5":
			menuUser()
		default:
			fmt.Println("  Opción no válida")
			pauseGo()
		}
	}
}

func menuRedes() {
	for {
		bannerGo()
		showMenu([][2]string{{"1", "DNS"}, {"2", "Ping"}, {"3", "Escaneo puertos"}, {"4", "Traceroute"}, {"5", "Subred"}, {"0", "Volver"}})
		c := ask("Elige")
		if c == "0" {
			return
		}
		switch c {
		case "1":
			printMap(dnsCore(ask("Host")))
		case "2":
			fmt.Println(pingCore(ask("Host")))
		case "3":
			if !confirmGo() {
				fmt.Println("  Escaneo cancelado.")
				break
			}
			host := ask("Host/IP")
			pr := ask("Puertos (ej. 22,80,443 o 1-1024)")
			plist, err := parsePorts(pr)
			if err != nil {
				fmt.Println("  [!]", err)
				break
			}
			fmt.Println("  Escaneando...")
			ip, res := scanCore(host, plist, 1000, 100)
			fmt.Println("  IP:", ip)
			keys := make([]string, 0, len(res))
			for k := range res {
				keys = append(keys, k)
			}
			sort.Strings(keys)
			for _, k := range keys {
				if open, _ := res[k]["open"].(bool); open {
					fmt.Printf("   puerto %s : %sABIERTO%s -> %v\n", k, ng, end, res[k]["banner"])
				} else {
					fmt.Printf("   puerto %s : cerrado\n", k)
				}
			}
		case "4":
			fmt.Println("  (usa: darkly-go traceroute <host>)")
		case "5":
			if out, err := subnetCore(ask("CIDR (ej. 192.168.1.0/24)")); err != nil {
				fmt.Println("  [!]", err)
			} else {
				printMap(out)
			}
		default:
			fmt.Println("  Opción no válida")
		}
		pauseGo()
	}
}

func menuSeg() {
	for {
		bannerGo()
		showMenu([][2]string{{"1", "Hash"}, {"2", "Identificar hash"}, {"3", "Auditoría contraseña"}, {"4", "Generar contraseña"}, {"5", "Cabeceras URL"}, {"6", "Analizar URL"}, {"0", "Volver"}})
		c := ask("Elige")
		if c == "0" {
			return
		}
		switch c {
		case "1":
			t := ask("Texto")
			a := ask("Algoritmo [sha256]")
			if a == "" {
				a = "sha256"
			}
			fmt.Printf("  Usa: darkly-go hash --algo %s %s\n", a, t)
		case "2":
			fmt.Println("  Usa: darkly-go hashid <hash>")
		case "3":
			fmt.Print("  Contraseña (se verá en pantalla): ")
			pw, _ := reader.ReadString('\n')
			pw = strings.TrimSpace(pw)
			f := passStrength(pw)
			fmt.Println("  Nivel:", f.Nivel)
			n, err := breachCore(pw)
			if err != nil {
				fmt.Println("  Filtración no verificable:", err)
			} else if n > 0 {
				fmt.Printf("  NO USAR: filtrada %d veces.\n", n)
			} else {
				fmt.Println("  Sin filtraciones conocidas.")
			}
		case "4":
			fmt.Println("  Usa: darkly-go genpass --n 16")
		case "5":
			printMap(headersCore(ask("URL")))
		case "6":
			fmt.Println("  Usa: darkly-go urlscan <url>")
		default:
			fmt.Println("  Opción no válida")
		}
		pauseGo()
	}
}

func menuIP() {
	for {
		bannerGo()
		showMenu([][2]string{{"1", "Geo por IP"}, {"2", "PTR"}, {"3", "RDAP"}, {"4", "Informe completo"}, {"0", "Volver"}})
		c := ask("Elige")
		if c == "0" {
			return
		}
		switch c {
		case "1":
			printMap(geoCore(ask("IP")))
		case "2":
			fmt.Println("  PTR:", ptrCore(ask("IP")))
		case "3":
			printMap(rdapCore(ask("Dominio/IP")))
		case "4":
			fmt.Println("  Usa: darkly-go report --ip 8.8.8.8 --nombre casa")
		default:
			fmt.Println("  Opción no válida")
		}
		pauseGo()
	}
}

func menuSys() {
	bannerGo()
	host, _ := os.Hostname()
	fmt.Println("  Host:", host, "| Disco:", diskInfo())
	pauseGo()
}

func menuUser() {
	u := ask("Nombre de usuario (sin @)")
	fmt.Println("  Buscando en 17 sitios (tarda ~30s)...")
	res := userSearch(u)
	hits := 0
	for _, r := range res {
		if strings.HasPrefix(r.Estado, "posible perfil") {
			hits++
			fmt.Printf("   [+] %s: %s (%s)\n", r.Sitio, r.URL, r.Estado)
		}
	}
	fmt.Printf("  Posibles: %d/%d\n", hits, len(res))
	pauseGo()
}
