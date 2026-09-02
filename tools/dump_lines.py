import os
import re
import sys
import json
import pprint
import hashlib
import argparse

sys.path.append('./modules')
from pdf_parser import PdfParser
from parser_factory import parserConfigs

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
EXIT_SENSITIVE = 3

EPILOG = """\
examples:
  tools/dump_lines.py files/releve-fortuneo.pdf --name fortuneo_lines_1 \\
      --output tests/files/releve_fortuneo_1.py
  tools/dump_lines.py files/releve-fortuneo.pdf --name x --output f.py --dry-run
  tools/dump_lines.py --check tests/files/

Anonymisation is on by default because tests/files/ is committed. --no-anonymise
is for local work only: the raw dump carries the account holder's name, IBAN,
BIC, address and every counterparty.

It is a helper, not a guarantee. The rules key off structure — a civility before a
name, 'IBAN' before an account number, 'VIR SEPA' before a counterparty — so a bare
name with nothing in front of it is invisible to them, and so is the same name in
--check. Read the fixture before committing it, and pass --scrub 'THE NAME' for
anything the patterns missed. --scrub is repeatable and uses the same stable
pseudonyms, so a name scrubbed this way stays consistent across lines.

Prefer --output over shell redirection. 'docker compose run' allocates a TTY by
default and will inject control characters into a redirected stream; pass -T if
you redirect anyway:

  docker compose run --rm -T tests python tools/dump_lines.py ...

Every module appends './modules' to sys.path, so this only works when run from
the repository root.

--expected writes the parser's own output as the expected-results JSON. A golden
file produced by the code under test proves nothing about correctness: it freezes
current behaviour, including current bugs. Eyeball it against the real PDF once
before committing it. As an independent check, --expected reconciles the parsed
total against the statement's own ANCIEN SOLDE / TOTAL DES OPERATIONS / NOUVEAU
SOLDE rows when the statement has them, and refuses to write on a mismatch.

exit codes:
  0  success
  1  the dump, the parse or the reconciliation failed
  2  bad usage
  3  --check found something that looks like personal data
"""

FAKE_IBAN = 'FR7630001007941234567890185'
FAKE_BIC = 'AAAAFRPPXXX'
FAKE_POSTCODE = '75001'
FAKE_TOWN = 'VILLE EXEMPLE'
FAKE_ACCOUNT = '00000 00000 00000000000 00'

PSEUDONYMS = (
    'DUPONT',
    'MARTIN LUC',
    'BERNARD ANNE',
    'PETIT',
    'MOREAU CLAIRE',
    'LEROY',
    'GIRAUD PAUL',
    'ROUSSEL MARIE',
    'FONTAINE',
    'MERCIER JEAN',
    'BLANCHARD SOPHIE',
    'CHEVALIER',
)

# Structure the parsers match on. Masked before scrubbing so no rule can rewrite it.
PROTECTED_PHRASES = (
    'DATE DE VALEUR',
    'DETAIL DES OPERATIONS EN EUROS',
    'DÉTAIL DES OPÉRATIONS EN EUROS',
    'TOTAL DES OPERATIONS DU RELEVE',
    'TOTAL DES OPÉRATIONS DU RELEVÉ',
    'ANCIEN SOLDE',
    'NOUVEAU SOLDE',
    'CREDITEUR',
    'CRÉDITEUR',
    'DEBITEUR',
    'DÉBITEUR',
    'OPERATION',
    'OPÉRATION',
    'CREDIT',
    'CRÉDIT',
    'DEBIT',
    'DÉBIT',
    'DATE',
)

# Deliberately not protected: the literal 'IBAN' and 'BIC' prefixes. Masking them
# would hide the prefix BIC_REGEX anchors on, and no scrubber can match them anyway
# (both are far shorter than the 10 characters REFERENCE_REGEX needs).

DATE_PATTERN = r'\d{1,2}/\d{2}(?:/\d{2,4})?'
# \u00a0 and \u202f: statements use non-breaking and narrow no-break spaces
# as thousands separators, and they are invisible in an editor.
AMOUNT_PATTERN = '\\d[\\d\u00a0\u202f .]*,\\d{2}'

PROTECTED_REGEX = re.compile(
    '|'.join([DATE_PATTERN, AMOUNT_PATTERN] + [re.escape(phrase) for phrase in PROTECTED_PHRASES]),
    re.IGNORECASE
)

PLACEHOLDER_REGEX = re.compile('\x00(\\d+)\x00')

IBAN_REGEX = re.compile(r'[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}')
BIC_REGEX = re.compile(r'(BIC\s*:?\s*)([A-Z]{6}[A-Z0-9]{2,5})\b')
ACCOUNT_REGEX = re.compile(r'\d{5}\s\d{5}\s\d{11}\s\d{2}')
CIVILITY_REGEX = re.compile(r'\b(M|MR|MME|MLLE)\s+([A-ZÀ-Ÿ][A-ZÀ-Ÿ\'-]+(?:\s+[A-ZÀ-Ÿ\'-]+)*)')
REFERENCE_REGEX = re.compile(r'\b[A-Z0-9]{10,}\b')
TOWN_REGEX = re.compile(r'\b\d{5}\s+[A-ZÀ-Ÿ][A-ZÀ-Ÿ -]+(?:\s*\d+)?')
CIVILITIES = ('M', 'MR', 'MME', 'MLLE')
# The tail must hold a word of two letters or more: after the person rule has run, what
# is left after 'VIR INST' can be a bare 'M ' in front of an already-replaced name, and
# pseudonymising that fragment produces a second name glued onto the first.
COUNTERPARTY_REGEX = re.compile(r'\b(VIR SEPA|VIR INST|VIR DE|PRLV|CB)\s+([^\x00]*[A-ZÀ-Ÿa-zà-ÿ]{2,}[^\x00]*)')

class Anonymiser:
    """Rewrites the text of each cell, never its coordinates or its structure."""

    def __init__(self, literals=()):
        self.counts = {}
        self.pseudonyms = {}
        self.literalRegex = None

        if literals:
            self.literalRegex = re.compile(
                '|'.join(re.escape(literal) for literal in sorted(literals, key=len, reverse=True)),
                re.IGNORECASE
            )

    def anonymiseLines(self, lines):

        return [[self.anonymiseCell(cell) for cell in line] for line in lines]

    def anonymiseCell(self, cell):
        anonymised = dict(cell)
        anonymised['value'] = self.anonymiseValue(cell['value'])

        return anonymised

    def anonymiseValue(self, value):
        self.spans = []
        masked = PROTECTED_REGEX.sub(lambda match: self.protect(match.group(0)), value)

        for name, regex, replace in self.scrubbers():
            masked, count = regex.subn(replace, masked)
            if count:
                self.counts[name] = self.counts.get(name, 0) + count

        return self.unmask(masked)

    def scrubbers(self):
        # --scrub runs first: it is the operator naming something the patterns cannot see.
        named = [('named value', self.literalRegex, self.replaceNamed)] if self.literalRegex else []

        return tuple(named) + (
            ('iban', IBAN_REGEX, self.replaceIban),
            ('bic', BIC_REGEX, self.replaceBic),
            ('account number', ACCOUNT_REGEX, lambda match: self.protect(FAKE_ACCOUNT)),
            ('person', CIVILITY_REGEX, self.replacePerson),
            ('counterparty', COUNTERPARTY_REGEX, self.replaceCounterparty),
            ('postcode and city', TOWN_REGEX,
             lambda match: self.protect(FAKE_POSTCODE + ' ' + FAKE_TOWN)),
            ('reference', REFERENCE_REGEX, self.replaceReference),
        )

    def protect(self, text):
        """Park text behind a \\x00<index>\\x00 placeholder so no later rule can match it.

        Used both for the structure that must survive untouched and for the fakes the
        scrubbers insert: without it the reference rule rewrites the BIC that the BIC
        rule just wrote, because a fake BIC is also eleven capitals in a row.
        """
        self.spans.append(text)

        return '\x00%d\x00' % (len(self.spans) - 1)

    def unmask(self, value):
        while PLACEHOLDER_REGEX.search(value):
            value = PLACEHOLDER_REGEX.sub(lambda match: self.spans[int(match.group(1))], value)

        return value

    def replaceIban(self, match):
        fake = []
        index = 0
        for character in match.group(0):
            if character.isspace():
                fake.append(character)
            else:
                fake.append(FAKE_IBAN[index % len(FAKE_IBAN)])
                index += 1

        return self.protect(''.join(fake))

    def replaceBic(self, match):

        return match.group(1) + self.protect(FAKE_BIC[:len(match.group(2))])

    def replacePerson(self, match):

        return match.group(1) + ' ' + self.protect(self.pseudonym(match.group(2)))

    def replaceCounterparty(self, match):
        counterparty = match.group(2).strip()
        civility = ''
        words = counterparty.split(None, 1)

        if words and words[0].upper() in CIVILITIES:
            civility = words[0] + ' '
            counterparty = words[1] if len(words) > 1 else ''

        if not counterparty:

            return match.group(0)

        return match.group(1) + ' ' + civility + self.protect(self.pseudonym(counterparty))

    def replaceNamed(self, match):

        return self.protect(self.pseudonym(match.group(0)))

    def replaceReference(self, match):
        original = match.group(0)
        digest = hashlib.sha256(original.encode('utf-8')).hexdigest().upper()

        return self.protect(digest[:len(original)])

    def pseudonym(self, text):
        """Same input always yields the same fake name, so a label split across
        several lines stays coherent once the parser joins it back together."""
        key = ' '.join(text.split()).upper()

        if key not in self.pseudonyms:
            closest = sorted(PSEUDONYMS, key=lambda name: (abs(len(name) - len(key)), name))[:3]
            digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
            self.pseudonyms[key] = closest[int(digest, 16) % len(closest)]

        return self.pseudonyms[key]

    def summary(self):
        if not self.counts:

            return 'Anonymisation: nothing matched.'

        parts = ['%s: %d' % (name, self.counts[name]) for name in sorted(self.counts)]

        return 'Anonymisation replaced ' + ', '.join(parts)

AMOUNT_ONLY_REGEX = re.compile('^-?' + AMOUNT_PATTERN + r'\s*€?$')

def parse_amount(text):
    cleaned = text.replace('€', '')
    for space in (' ', ' ', ' ', '.'):
        cleaned = cleaned.replace(space, '')

    return float(cleaned.replace(',', '.'))

def line_text(line):

    return ' '.join(cell['value'] for cell in line)

def find_line(lines, *labels):
    for line in lines:
        text = line_text(line).upper()
        for label in labels:
            if label in text:

                return line

    return None

def amounts_in(line):

    return [parse_amount(cell['value']) for cell in line if AMOUNT_ONLY_REGEX.match(cell['value'].strip())]

def amounts_match(computed, expected):
    """Binary floats do not sum exactly, so compare to the cent, never with ==."""

    return abs(round(computed, 2) - round(expected, 2)) < 0.005

def reconcile(lines, transactions):
    """Check the parsed transactions against the statement's own summary rows.

    Returns a message, or None when the statement carries no such rows: not every
    bank prints them, and a missing anchor is not a failure. Raises on a mismatch.
    """
    openingLine = find_line(lines, 'ANCIEN SOLDE')
    closingLine = find_line(lines, 'NOUVEAU SOLDE')

    if openingLine is None or closingLine is None:

        return None

    opening = signed_balance(openingLine)
    closing = signed_balance(closingLine)

    if opening is None or closing is None:

        return None

    values = [transaction['value'] for transaction in transactions]

    if not amounts_match(sum(values), closing - opening):
        raise Exception(
            'Reconciliation failed: the transactions sum to %.2f but the statement goes from %.2f '
            'to %.2f, a difference of %.2f. The parse is wrong, or a row was missed.'
            % (sum(values), opening, closing, closing - opening)
        )

    totalsLine = find_line(lines, 'TOTAL DES OPERATIONS', 'TOTAL DES OPÉRATIONS')
    if totalsLine is not None:
        totals = amounts_in(totalsLine)
        if len(totals) == 2:
            debitTotal, creditTotal = totals
            debits = sum(value for value in values if value < 0)
            credits = sum(value for value in values if value > 0)
            if not amounts_match(-debits, debitTotal) or not amounts_match(credits, creditTotal):
                raise Exception(
                    'Reconciliation failed: parsed debits %.2f and credits %.2f against the '
                    'statement\'s %.2f and %.2f. The balance can still add up when two errors '
                    'cancel, which is why this is checked separately.'
                    % (-debits, credits, debitTotal, creditTotal)
                )

            return ('Reconciled: %d transactions, balance %.2f -> %.2f, debits %.2f, credits %.2f'
                    % (len(transactions), opening, closing, debitTotal, creditTotal))

    return ('Reconciled: %d transactions take the balance from %.2f to %.2f'
            % (len(transactions), opening, closing))

def signed_balance(line):
    """The amount is printed unsigned; DEBITEUR on the same row is what makes it negative."""
    amounts = amounts_in(line)

    if not amounts:

        return None

    balance = amounts[-1]
    text = line_text(line).upper()

    if 'DEBITEUR' in text or 'DÉBITEUR' in text:

        return -balance

    return balance

def format_fixture(lines, name, source, anonymised):
    header = [
        '# Generated by tools/dump_lines.py from %s — do not edit by hand' % source,
        '# Anonymised: %s' % ('yes' if anonymised else 'NO, this holds raw statement data'),
    ]
    body = '%s = %s' % (name, pprint.pformat(lines, sort_dicts=False, width=100))

    return '\n'.join(header) + '\n\n' + body + '\n'

def read_lines(file_path):
    pdfFile = open(file_path, 'rb')
    try:
        return PdfParser().parse(pdfFile)
    finally:
        pdfFile.close()

CHECK_REGEXES = (
    ('iban', IBAN_REGEX),
    ('bic', BIC_REGEX),
    ('account number', ACCOUNT_REGEX),
    ('person', CIVILITY_REGEX),
    ('postcode and city', TOWN_REGEX),
    ('reference', REFERENCE_REGEX),
)

def known_fakes():
    fakes = [FAKE_IBAN, FAKE_BIC, FAKE_ACCOUNT, FAKE_POSTCODE + ' ' + FAKE_TOWN, FAKE_TOWN]

    return [fake.replace(' ', '') for fake in fakes + list(PSEUDONYMS)]

def is_allowed(text, allowList):
    compact = text.replace(' ', '').replace(' ', '')

    for fake in known_fakes():
        if fake and fake in compact:

            return True

    for entry in allowList:
        if entry and entry in text:

            return True

    return False

def mask_finding(text):
    """Never print the match itself: --check output ends up in CI logs."""
    stripped = text.strip()

    return '%s… (%d characters)' % (stripped[:2], len(stripped))

def check_directory(directory, allowList):
    findings = []

    for root, _, fileNames in os.walk(directory):
        for fileName in sorted(fileNames):
            if not fileName.endswith('.py'):
                continue
            path = os.path.join(root, fileName)
            with open(path, encoding='utf-8') as fixture:
                for number, text in enumerate(fixture, start=1):
                    for name, regex in CHECK_REGEXES:
                        for match in regex.finditer(text):
                            if not is_allowed(match.group(0), allowList):
                                findings.append((path, number, name, mask_finding(match.group(0))))

    return findings

def read_allow_list(path):
    if path is None:

        return []

    with open(path, encoding='utf-8') as allowFile:

        return [line.strip() for line in allowFile if line.strip() and not line.startswith('#')]

def build_argument_parser():
    argumentParser = argparse.ArgumentParser(
        prog='tools/dump_lines.py',
        description='Turn a statement PDF into a paste-ready test fixture, anonymised by default.',
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    argumentParser.add_argument(
        'pdf_path',
        nargs='?',
        help='the statement to dump; not used with --check'
    )
    argumentParser.add_argument(
        '--name',
        help='the variable name to assign in the generated module, e.g. fortuneo_lines_1'
    )
    argumentParser.add_argument(
        '--output',
        help='where to write the fixture; required unless --dry-run'
    )
    argumentParser.add_argument(
        '--no-anonymise',
        dest='anonymise',
        action='store_false',
        help='write the statement verbatim; for local use only, never for a committed fixture'
    )
    argumentParser.add_argument(
        '--scrub',
        action='append',
        default=[],
        metavar='TEXT',
        help='also replace this literal text, e.g. an account holder name that no pattern can '
             'recognise; may be used more than once'
    )
    argumentParser.add_argument(
        '--dry-run',
        action='store_true',
        help='report what would be replaced without writing anything'
    )
    argumentParser.add_argument(
        '--expected',
        help='also write the parser output for the anonymised fixture, as expected-results JSON'
    )
    argumentParser.add_argument(
        '--parser',
        help='which parser --expected should run; see parse.py --list'
    )
    argumentParser.add_argument(
        '--check',
        metavar='DIRECTORY',
        help='re-run the sensitive-data patterns over the committed fixtures and exit non-zero on a hit'
    )
    argumentParser.add_argument(
        '--allow-list',
        help='file of literal strings --check should ignore, one per line'
    )

    return argumentParser

def run_check(arguments):
    findings = check_directory(arguments.check, read_allow_list(arguments.allow_list))

    if not findings:
        print('No personal data found in ' + arguments.check)

        return EXIT_OK

    for path, number, name, masked in findings:
        print('%s:%d: possible %s: %s' % (path, number, name, masked), file=sys.stderr)

    print(
        '\n%d possible leaks. Regenerate the fixture with tools/dump_lines.py, or add a literal to '
        '--allow-list if it is a false positive.' % len(findings),
        file=sys.stderr
    )

    return EXIT_SENSITIVE

def write_expected(lines, arguments):
    parserConfig = parserConfigs[arguments.parser]

    if parserConfig['type'] != 'pdf':
        raise Exception('--expected needs a pdf parser, and ' + arguments.parser + ' reads a file path')

    transactions = parserConfig['module'](lines).parse()
    reconciliation = reconcile(lines, transactions)

    if reconciliation is None:
        print('Reconciliation skipped: this statement has no ANCIEN SOLDE / NOUVEAU SOLDE rows. '
              'Check the expected results against the PDF by eye before committing them.')
    else:
        print(reconciliation)

    with open(arguments.expected, 'w', encoding='utf-8') as expectedFile:
        expectedFile.write(json.dumps(transactions, indent=4, sort_keys=True, ensure_ascii=False) + '\n')

    print('Wrote %d transactions to %s' % (len(transactions), arguments.expected))

def main(argv=None):
    argumentParser = build_argument_parser()
    arguments = argumentParser.parse_args(argv)

    if arguments.check:

        return run_check(arguments)

    if arguments.pdf_path is None or arguments.name is None:
        argumentParser.print_usage(sys.stderr)
        print('tools/dump_lines.py: error: a pdf and --name are required, or --check', file=sys.stderr)

        return EXIT_USAGE

    if arguments.output is None and not arguments.dry_run:
        print('tools/dump_lines.py: error: --output is required unless --dry-run', file=sys.stderr)

        return EXIT_USAGE

    if arguments.expected and not arguments.parser:
        print('tools/dump_lines.py: error: --expected needs --parser', file=sys.stderr)

        return EXIT_USAGE

    if arguments.parser and arguments.parser not in parserConfigs:
        print('Unknown parser with name ' + arguments.parser, file=sys.stderr)
        print('Available parsers: ' + ', '.join(parserConfigs), file=sys.stderr)

        return EXIT_USAGE

    try:
        lines = read_lines(arguments.pdf_path)

        if arguments.anonymise:
            anonymiser = Anonymiser(arguments.scrub)
            lines = anonymiser.anonymiseLines(lines)
            print(anonymiser.summary())
            print('Read the fixture before committing it: a name with no civility in front of it '
                  'matches no rule here, and --check will not see it either. Use --scrub for those.')
        else:
            print('Anonymisation: SKIPPED. Do not commit this fixture.')

        fixture = format_fixture(
            lines,
            arguments.name,
            os.path.basename(arguments.pdf_path),
            arguments.anonymise
        )

        if arguments.dry_run:
            print('Dry run: %d lines, %d cells, nothing written.'
                  % (len(lines), sum(len(line) for line in lines)))

            return EXIT_OK

        with open(arguments.output, 'w', encoding='utf-8') as fixtureFile:
            fixtureFile.write(fixture)

        print('Wrote %d lines to %s' % (len(lines), arguments.output))

        if arguments.expected:
            write_expected(lines, arguments)

    except Exception as error:
        print(error, file=sys.stderr)

        return EXIT_FAILURE

    return EXIT_OK

if __name__ == '__main__':
    sys.exit(main())
