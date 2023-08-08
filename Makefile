.PHONY: test
test:
	@go test -v ./...


.PHONY: lint
lint:
	@go fmt ./...
	@go vet ./...
	@go fix ./...
