help:
	@echo "Current solutions:"
	@ls -1 */* | sed "s;/main.;-;g" | sort | xargs -I {} echo "    - {}"
	@echo "\nRun a solution:\n    make smoke-test-go"

ip:
	curl icanhazip.com

smoke-test-go:
	go run smoke-test/main.go

smoke-test-py:
	python smoke-test/main.py

prime-time-py:
	python prime-time/main.py

means-to-an-end-py:
	python means-to-an-end/main.py

.PHONY: ip smoke-test-go smoke-test-py prime-time-py means-to-an-end-py
