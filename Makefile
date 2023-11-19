ip:
	curl icanhazip.com

smoke-test-go:
	go run smoke-test/main.go

smoke-test-py:
	python smoke-test/main.py

prime-time-py:
	python prime-time/main.py

.PHONY: ip smoke-test-go smoke-test-py prime-time-py
