package main

import (
	"fmt"
	"log/slog"
	"os"
)

var scripts = map[string]func(){
	"smoke-test": SmokeTest,
	"prime-time": PrimeTime,
	// "P2":  P2,
	// "P3":  P3,
	// "P4":  P4,
	// "P5":  P5,
	// "P6":  P6,
	// "P7":  P7,
	// "P8":  P8,
	// "P9":  P9,
	// "P10": P10,
}

func printAvailableScripts() {
	fmt.Println("Available scripts:")
	for name := range scripts {
		fmt.Println("\t- " + name)
	}
}

func main() {
	logger := slog.Default()
	if len(os.Args) != 2 {
		fmt.Println("Expected 1 command line argument: script to run")
		printAvailableScripts()
		os.Exit(1)
	}
	script, ok := scripts[os.Args[1]]
	if !ok {
		fmt.Println("Script not found:", os.Args[1])
		printAvailableScripts()
		os.Exit(1)
	}
	logger.Info("Running Script", "name", os.Args[1])
	script()
}
