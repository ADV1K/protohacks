smoke-test-go: ip
	go run smoke-test/main.go

ip:
	curl icanhazip.com

.PHONY: ip smoke-test-go
