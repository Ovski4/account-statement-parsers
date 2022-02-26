Account statement parsers
=========================

[![Build Status](https://travis-ci.org/Ovski4/account-statement-parsers.svg?branch=master)](https://travis-ci.org/Ovski4/account-statement-parsers) [![Coverage Status](https://coveralls.io/repos/github/Ovski4/account-statement-parsers/badge.svg?branch=master)](https://coveralls.io/github/Ovski4/account-statement-parsers?branch=master)

This repo provides modules used to extract transactions from account statement pdf files.

Currently support :
 - **Crédit Mutuel** pdf account statement files
 - **Caisse d'Épargne** pdf account statement files
 - **N26** pdf account statement files
 - **Boursorama** pdf account statement files
 - **NBC** csv export files

Usage
-----

The run_api.py script runs a simple http server that will return transactions as JSON.

```bash
docker-compose run --service-ports api

curl -H "Accept: application/json" -X GET 127.0.0.1/credit-mutuel?statement=/path/to/statement.pdf
```

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
