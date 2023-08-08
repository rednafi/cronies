.PHONY: build
	@go build .

.PHONY: test
	@go test -v ./...

.PHONY: run
	@go run .

.PHONY: clean
	@rm -f $(BINARY_NAME)

.PHONY: lint
	@golangci-lint run
