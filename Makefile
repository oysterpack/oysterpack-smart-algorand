pre-commit: format check localnet-reset test

test:
	coverage run -m unittest
	coverage html
	coverage report

format:
	black oysterpack
	black tests

# enforces style guide
check:
	ruff check oysterpack --fix
	mypy oysterpack
	ruff check tests --fix
	mypy tests

pydoc:
	poetry run python -m pydoc -b

# algorand node commands depend on the $ALGORAND_DATA env var
# if not set, then it defaults to /var/lib/algorand
check_algorand_data_env_var:
ALGORAND_DATA ?= "/var/lib/algorand"

algod-status: check_algorand_data_env_var
	sudo -u algorand goal -d $(ALGORAND_DATA) node status

kmd-start: check_algorand_data_env_var
	sudo -u algorand goal -d $(ALGORAND_DATA) kmd start

kmd-stop: check_algorand_data_env_var
	sudo -u algorand goal -d $(ALGORAND_DATA) kmd stop

localnet-reset:
	algokit localnet reset