# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Everything runs in Docker (Python 3, deps from `requirements.txt`):

```bash
docker compose run tests                  # full test suite (pytest --cov=modules tests/)
docker compose run --service-ports api    # HTTP API on port 80
```

Run a single test locally or inside the container — always from the repo root, since tests use
relative paths (`./modules`, `./tests/files`):

```bash
pytest tests/test_boursorama_statement_parser.py
pytest tests/test_boursorama_statement_parser.py::testIsDebitLine
```

Remote debugging (ptvsd, port 3000): `docker compose run -e DEBUG=true --service-ports tests`,
then attach the VS Code debugger (config in README.md). Each test file has a `DEBUG=true` guard that blocks on `ptvsd.wait_for_attach()`.

API usage (paths are resolved inside the container):

```bash
curl "127.0.0.1/boursorama?statement=files/releve-boursorama.pdf"
curl "127.0.0.1/boursorama/balance?statement=files/releve-boursorama.pdf"
```

## Architecture

The repo extracts transactions from bank account statements and returns them as JSON. There is no package structure — `modules/` is put on `sys.path` (`sys.path.append('modules')`), so imports are flat (`from pdf_parser import PdfParser`).

### Two parser families

**PDF parsers** (Crédit Mutuel, Caisse d'Épargne, N26, Boursorama). `PdfParser` (`modules/pdf_parser.py`) is the shared front end: pdfminer.six extracts text runs with bounding boxes, then `PDFPageDetailedAggregator` collects them as `(page, x0, y0, x1, y1, text)` cells sorted by page then descending y, and `groupLines` groups cells into visual lines (same y within `LINE_THRESHOLD = 10`), each line sorted left-to-right. The output — and the input every bank
parser takes in its constructor — is:

```python
lines = [[{'value': str, 'x0': float, 'y0': float, 'x1': float, 'y1': float}, ...], ...]
```

Each bank parser is a standalone class (no shared base) that walks these lines with a small state
machine. The recurring shape:

- detect a header-table line by its literal French column labels (e.g. `'débit euros'`), and store
  the x-boundaries of each column from that line (`getColumnBoundaries`) — column positions are
  learned per document rather than hardcoded. Boursorama is the exception: its boundaries are
  hardcoded in `__init__`.
- detect an account line to set the current account, applied to subsequent transactions.
- classify a line as debit or credit by checking each word's x-range against the stored column
  boundaries (`linesAreWithinBoundaries`, with a per-parser tolerance margin).
- after extracting a transaction, keep consuming the following single-word lines that fall in the
  label/operation column and append them to the label (multi-line descriptions).
- pre-pass filtering: Crédit Mutuel strips the vertical decorative line on the left
  (`isVerticalLeftSideWord`), Caisse d'Épargne drops everything with `x0 < 30`.

**CSV parsers** (NBC). `NBCCsvParser` is an actual base class: it reads the `;`-delimited file, infers the file type from the header row (`guessFileTypeFromHeader`), raises if that type does not match the subclass's `getFileType()`, and delegates each row to the subclass's `extractDataFromRow`. Subclasses differ only in column indices, because the credit-card export has an extra card-number column. These parsers take a **file path**, not lines.

### Output contract

Every parser's `parse()` returns a list of dicts. PDF parsers emit `{'account', 'date', 'label', 'value'}`; NBC CSV parsers emit `{'date', 'label', 'value'}` (no account). Dates are `dd/mm/yyyy`. `value` is a signed float — negative for debits, positive for credits — and amounts in French format (`1.473,00`) are converted by stripping `.` and swapping
`,` for `.`.

### API layer

`run_api.py` is a Klein (Twisted) server. `parserConfigs` maps the URL slug to `{module, type}`;
`type` decides whether the file is run through `PdfParser` first (`'pdf'`) or handed to the parser as a path (`'csv'`). Adding a parser means adding a module in `modules/`, importing it, and adding one `parserConfigs` entry — routes are generic (`/<parser_name>` and `/<parser_name>/balance`).

## Tests

PDF parsers are **not** tested against PDFs. The pdfminer output is frozen as a Python literal in `tests/files/releve_*.py` (e.g. `boursorama_lines_1`), imported directly, and the parsed result is compared to `tests/files/expected-results-*.json`. So a new PDF parser needs a captured `lines` fixture (dump `PdfParser().parse(f)` for a real statement) plus its expected JSON. Only `test_pdf_parser.py` reads an actual PDF (`tests/files/test.pdf`).

CSV parsers are tested against real CSV fixtures in `tests/files/`.

Fixture statements contain real bank data, so `/files` and `/tests` are gitignored from the Docker image; keep personal statements out of commits.

## Conventions

Code is camelCase throughout (`extractDataFromRow`, `isDebitLine`, `currentColumnBoundaries`), which is unusual for Python but consistent — match it. Parsers, their tests, and their route slugs are named after the bank (`boursorama_statement_parser.py` → `tests/test_boursorama_statement_parser.py` → `/boursorama`).
