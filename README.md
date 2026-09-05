Account statement parsers
=========================

[![Tests](https://github.com/Ovski4/account-statement-parsers/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/Ovski4/account-statement-parsers/actions/workflows/tests.yml) [![Coverage Status](https://coveralls.io/repos/github/Ovski4/account-statement-parsers/badge.svg?branch=master)](https://coveralls.io/github/Ovski4/account-statement-parsers?branch=master)

This repo provides modules used to extract transactions from account statement pdf files.

Currently support :
 - **Crédit Mutuel** pdf account statement files
 - **Caisse d'Épargne** pdf account statement files
 - **N26** pdf account statement files
 - **Boursorama** pdf account statement files
 - **Fortuneo** pdf account statement files
 - **NBC** csv export files

Usage
-----

### From the command line

The parse.py script prints the transactions of a single statement as JSON:

```bash
docker compose run --rm tests python parse.py credit-mutuel files/releve-credit-mutuel.pdf
docker compose run --rm tests python parse.py credit-mutuel files/releve-credit-mutuel.pdf --balance
docker compose run --rm tests python parse.py --list
```

It exits non-zero on failure, with the error on stderr and JSON on stdout only, so it can be
used from scripts. Run `python parse.py --help` for the full options and exit codes.

### As an http api

The run_api.py script runs a simple http server that will return transactions as JSON.

```bash
docker compose run --service-ports api
curl -H "Accept: application/json" -X GET 127.0.0.1/credit-mutuel?statement=/path/to/statement.pdf
```

Example:

```
# Create a folder and add your file in it
mkdir -p files
cp ../some/path/boursorama-statement.pdf files/releve-boursorama.pdf

# Exec in the container and request the api
docker exec -it `container_id` bash
curl -H "Accept: application/json" -X GET 127.0.0.1/boursorama?statement=files/releve-boursorama.pdf
```

Tests
-----

```bash
docker compose run tests
```

Debug with vscode
-----------------

Install the [python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python).

Create the vscode debugger configuration. Hit `Ctrl+P` in VS Code, then type `>Debug: Add Configuration`.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Remote debugging",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 3000
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "/usr/src/app"
                }
            ]
        }
    ]
}
```

Add your breakpoints, then run a script:

```bash
docker compose run --rm --service-ports tests python -m debugpy --listen 0.0.0.0:3000 --wait-for-client parse.py n26 files/n26-statement.pdf
```

Or run the tests:

```bash
docker compose run -e DEBUG=true --service-ports tests
```

The run blocks in `tests/conftest.py` until the debugger attaches, so start it from vscode
**only after that**, then the suite runs.
