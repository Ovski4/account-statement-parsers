# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Everything runs in Docker (Python pinned in the `Dockerfile`, deps pinned in `requirements.txt`):

```bash
docker compose run tests                  # full test suite (pytest --cov=modules tests/)
docker compose run --service-ports api    # HTTP API on port 80
```

Run a single test locally or inside the container — always from the repo root, since the paths
are relative (`./modules`, `./tests/files`):

```bash
pytest tests/test_boursorama_statement_parser.py
pytest tests/test_boursorama_statement_parser.py::testIsDebitLine
```

CLI entry point (`parse.py`), which prints the transactions of one statement as JSON:

```bash
docker compose run --rm tests python parse.py credit-mutuel files/releve-credit-mutuel.pdf
docker compose run --rm tests python parse.py credit-mutuel files/releve-credit-mutuel.pdf --balance
docker compose run --rm tests python parse.py --list
```

Exit codes: `0` success (JSON on stdout), `1` parse failure (message on stderr), `2` bad usage
including an unknown parser name.

API usage (paths are resolved inside the container):

```bash
curl "127.0.0.1/boursorama?statement=files/releve-boursorama.pdf"
curl "127.0.0.1/boursorama/balance?statement=files/releve-boursorama.pdf"
```

Remote debugging uses **debugpy** on port 3000. For the suite,
`docker compose run -e DEBUG=true --service-ports tests` — the `DEBUG=true` guard lives in
`tests/conftest.py` only (not in each test file) and blocks on `debugpy.wait_for_client()`; it
also sets `debugpy.configure(subProcess=False)` so the subprocesses `test_parse.py` spawns are
not debugged too. For a single script, run it under debugpy directly:

```bash
docker compose run --rm --service-ports tests python -m debugpy --listen 0.0.0.0:3000 --wait-for-client parse.py n26 files/n26-statement.pdf
```

The VS Code attach config is in `.vscode/launch.json`.

CI (`.github/workflows/tests.yml`) runs the suite on the host with `--cov-fail-under=98` and
separately builds the image and runs the suite inside it. The Python version there and the
Dockerfile's `FROM` must stay in sync.

## Architecture

The repo extracts transactions from bank account statements and returns them as JSON. There is no
package structure — `modules/` is put on `sys.path` (`sys.path.append('./modules')`, done by each
entry point and by `tests/conftest.py`), so imports are flat (`from pdf_parser import PdfParser`).

### Entry points and the factory

`parse.py` (CLI) and `run_api.py` (Klein/Twisted HTTP server) are thin: both call
`create_parser(file_path, parser_name)` from `modules/parser_factory.py` and then `parse()`.

`parser_factory.parserConfigs` maps the parser name — used both as the CLI argument and as the URL
slug — to `{module, type}`. `type` decides whether the file is run through `PdfParser` first
(`'pdf'`) or handed to the parser as a path (`'csv'`). **Adding a parser means adding a module in
`modules/`, importing it in `parser_factory.py`, and adding one `parserConfigs` entry** — the API
routes (`/<parser_name>` and `/<parser_name>/balance`) and the CLI are generic and pick it up.

`modules/transactions.py` holds `compute_balance(transactions)`, the shared total used by
`--balance`, the `/balance` route, and Fortuneo's self-check.

`modules/line_reader.py` holds `LineReader`, a one-method helper (`contains`) used by several PDF
parsers to test whether any word of a line holds a given substring.

### Two parser families

**PDF parsers** (Crédit Mutuel, Caisse d'Épargne, N26, Boursorama, Fortuneo). `PdfParser`
(`modules/pdf_parser.py`) is the shared front end: pdfminer.six extracts text runs with bounding
boxes, then `PDFPageDetailedAggregator` collects them as `(page, x0, y0, x1, y1, text)` cells
sorted by page then descending y, and `groupLines` groups cells into visual lines, each line then
sorted left-to-right. Grouping tracks the highest and lowest top the current group spans and
starts a new line when that span exceeds `LINE_THRESHOLD = 10`, rather than comparing each cell to
the group's first cell — otherwise a group could span twice the threshold and merge two rows. The
output — and the input every bank parser takes in its constructor — is:

```python
lines = [[{'value': str, 'x0': float, 'y0': float, 'x1': float, 'y1': float}, ...], ...]
```

Each bank parser is a standalone class (no shared base) that walks these lines with a small state
machine. The recurring shape:

- get the x-boundaries of each column. Crédit Mutuel and Caisse d'Épargne detect a header-table
  line by its literal French column labels (e.g. `'débit euros'`) and learn the boundaries from it
  per document (`getColumnBoundaries`). Boursorama and Fortuneo hardcode them instead — Fortuneo
  because it right-aligns amounts and left-aligns labels far from their headers, so the headers say
  nothing about where the columns are.
- detect an account line to set the current account, applied to subsequent transactions.
- classify a line as debit or credit by checking each word's x-range against the stored column
  boundaries (`linesAreWithinBoundaries` / `wordIsWithinBoundaries`, with a per-parser tolerance
  margin).
- after extracting a transaction, keep consuming the following single-word lines that fall in the
  label/operation column and append them to the label (multi-line descriptions).
- pre-pass filtering: Crédit Mutuel strips the vertical decorative line on the left
  (`isVerticalLeftSideWord`), Caisse d'Épargne drops everything with `x0 < 30`, Fortuneo drops
  everything with `x1 < 40` (`removeLeftMarginWords`) — that vertical margin text comes out one
  cell per character and some of those rows have exactly the 4-cell shape of a transaction row.

Fortuneo is the most defensive of the parsers and worth reading before writing a new one:

- because its boundaries are hardcoded rather than learned, and pages are not laid out at the same
  x (page 2 is shifted a few points right), it re-reads the repeated header row on every page and
  offsets the boundaries by the difference against
  `COLUMN_BOUNDARIES_MEASURED_AT_HEADER_DATE_X0`. Those two constants are a matched pair.
- the date column holds only a day and a month, so the year comes from the `Arrêté au …` statement
  period, minus one when the operation month is later than the statement month.
- `validateAgainstStatementBalance` cross-checks the parsed transactions against the statement's
  own `ANCIEN SOLDE` / `NOUVEAU SOLDE` / `TOTAL DES OPÉRATIONS` rows and raises otherwise, so a
  column drifting a few points fails loudly instead of silently flipping a sign. Missing IBAN or
  missing balance rows raise too.

**CSV parsers** (NBC). `NBCCsvParser` is an actual base class: it reads the `;`-delimited file,
infers the file type from the header row (`guessFileTypeFromHeader`), raises if that type does not
match the subclass's `getFileType()`, and delegates each row to the subclass's `extractDataFromRow`.
Subclasses differ only in column indices, because the credit-card export has an extra card-number
column. These parsers take a **file path**, not lines.

### Output contract

Every parser's `parse()` returns a list of dicts. PDF parsers emit
`{'account', 'date', 'label', 'value'}`; NBC CSV parsers emit `{'date', 'label', 'value'}` (no
account). Dates are `dd/mm/yyyy`. `value` is a signed float — negative for debits, positive for
credits — and amounts in French format (`1.473,00`) are converted by stripping `.` and swapping
`,` for `.`.

## Tests

`tests/conftest.py` puts `./modules` and `./tests/files` on `sys.path`, so test modules import
both the parsers and the fixtures directly, with no boilerplate of their own.

PDF parsers are **not** tested against PDFs. The pdfminer output is frozen as a Python literal in
`tests/files/releve_*.py` (e.g. `boursorama_lines_1`), imported directly, and the parsed result is
compared to `tests/files/expected-results-*.json`. So a new PDF parser needs a captured `lines`
fixture (dump `PdfParser().parse(f)` for a real statement) plus its expected JSON. Only
`test_pdf_parser.py` reads an actual PDF (`tests/files/test.pdf`).

Where a real statement cannot cover a branch, tests build synthetic lines instead:
`test_fortuneo_statement_parser.py` has `word` / `headerTableLine` / `transactionLine` /
`buildStatement` helpers, using x coordinates measured on the real statement, to cover the debit
column, the page-2 offset and the balance self-check that the credit-only sample never reaches.

CSV parsers are tested against real CSV fixtures in `tests/files/`. `test_parse.py` runs `parse.py`
as a subprocess and asserts on its stdout, stderr and exit codes.

Fixture statements contain real bank data: `/files` is gitignored, and `.dockerignore` keeps
`/tests` out of the image (CI and `docker-compose.yml` mount the repo to run the suite in the
container). Keep personal statements out of commits.

## Conventions

Class methods and their locals are camelCase (`extractDataFromRow`, `isDebitLine`,
`currentColumnBoundaries`), which is unusual for Python but consistent — match it inside the
parsers. The newer module-level functions and entry points use snake_case instead
(`create_parser`, `compute_balance`, `parse_statement`, `build_argument_parser`). Parsers, their
tests, and their names in `parserConfigs` are named after the bank
(`boursorama_statement_parser.py` → `tests/test_boursorama_statement_parser.py` → `boursorama`).

Non-obvious layout decisions are explained in block-comment docstrings above the method or
constant they concern (see `pdf_parser.groupLines`, `FortuneoStatementParser.COLUMN_BOUNDARIES`) —
follow that when adding one, because these numbers are measurements nobody can re-derive later.
