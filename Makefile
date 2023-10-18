help: ## Print this message and exit.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2 | "sort"}' $(MAKEFILE_LIST)


compile-requirements: ## Compile requirements (using pip-compile)
	pip-compile requirements.in.txt -o requirements.txt --no-emit-index-url -v

builddev:
	docker-compose build

run-lab:
	docker-compose run lab

generate: ## generate reports
	docker-compose run generator bash -c "python src/main.py"

generate-send: ## generate report and send it
	docker-compose run generator bash -c "python src/main.py --send=True"

