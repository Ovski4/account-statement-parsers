
Usage
-----

```bash
docker-compose run main
```

Tests
-----

```bash
docker-compose run tests
```

Debug
-----

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

Uncomment these lines in your test file:

```py
import ptvsd
ptvsd.enable_attach(address = ('0.0.0.0', 3000))
ptvsd.wait_for_attach()
```

Run the tests

```bash
docker-compose run --service-ports tests
```

And only after that, run the debugger in vscode
