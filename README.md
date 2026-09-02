Account statement parsers
=========================

[![Tests](https://github.com/Ovski4/account-statement-parsers/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/Ovski4/account-statement-parsers/actions/workflows/tests.yml) [![Coverage Status](https://coveralls.io/repos/github/Ovski4/account-statement-parsers/badge.svg?branch=master)](https://coveralls.io/github/Ovski4/account-statement-parsers?branch=master)

This repo provides modules used to extract transactions from account statement pdf files.

Currently support :
 - **Crédit Mutuel** pdf account statement files
 - **Caisse d'Épargne** pdf account statement files
 - **N26** pdf account statement files
 - **Boursorama** pdf account statement files
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
docker-compose run --service-ports api
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

Generating test fixtures
------------------------

`tools/dump_lines.py` turns a statement PDF into a `tests/files/releve_*.py` fixture, so a new
parser can be written against committed line data instead of a PDF that cannot be shared.

```bash
docker compose run --rm -T tests python tools/dump_lines.py files/releve-fortuneo.pdf \
    --name fortuneo_lines_1 --output tests/files/releve_fortuneo_1.py
```

Anonymisation is on by default, because `tests/files/` is committed: IBANs, BICs, names after a
civility, addresses and transfer references are replaced with stable fakes, while dates, amounts,
column headers and summary rows are left exactly as they are.

**It is a helper, not a guarantee.** The rules key off structure — a civility before a name, `IBAN`
before an account number — so a bare name with nothing in front of it matches nothing. Read the
fixture before committing it and pass `--scrub 'THE NAME'` for whatever the patterns missed.

```bash
# check committed fixtures for anything that looks like personal data
docker compose run --rm -T tests python tools/dump_lines.py --check tests/files/
```

`--check` exits 3 on a hit and prints the file and line without printing the value. Run
`python tools/dump_lines.py --help` for `--expected`, `--dry-run` and the rest.

Tests
-----

```bash
docker-compose run tests
```

Debug with vscode
-----------------

Create the vscode debugger configuration:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Remote debugging",
            "type": "python",
            "request": "attach",
            "pathMappings": [
                {
                    "localRoot": "${workspaceRoot}",
                    "remoteRoot": "/usr/src/app"
                }
            ],
            "port": 3000,
            "host": "localhost"
        }
    ]
}
```

Run the tests

```bash
docker-compose run -e DEBUG=true --service-ports tests
```

And **only after that**, run the debugger in vscode
