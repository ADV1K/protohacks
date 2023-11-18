smoke-test-py:
	python smoke-test/main.py

smoke-test-go:
	go run smoke-test/main.go

ip:
	curl icanhazip.com

.PHONY: ip smoke-test-go smoke-test-py
