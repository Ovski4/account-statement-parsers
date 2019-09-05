import sys
sys.path.append('./modules')
from linereader import LineReader

class CCMParser:

    def __init__(self, lines):
        self.lines = lines
        self.currentAccount = None
        self.data = []

    # def parse(self):

    def isHeaderTableLine(self, line):
        if (
            len(line) == 5 and
            line[0]['value'] == 'Date' and
            line[1]['value'] == 'Date valeur' and
            line[2]['value'] == 'Opération' and
            line[3]['value'] == 'Débit euros' and
            line[4]['value'] == 'Crédit euros'
        ):
            return True
        return False

    def getColumnBoundaries(self, line):
        boundaries = {}
        dictionnary = {
            'Date': 'date',
            'Date valeur': 'date_valeur',
            'Opération': 'operation',
            'Débit euros': 'debit',
            'Crédit euros': 'credit'
        }

        for word in line:
            boundaries[dictionnary[word['value']]] = {
                'x0': word['x0'],
                'x1': word['x1']
            }

        return boundaries

    def isAccountNameLine(self, lineIndex):
        line1Reader = LineReader(self.lines[lineIndex])
        if line1Reader.contains('en euros'):
            line2Reader = LineReader(self.lines[lineIndex + 1])
            if line2Reader.contains('TITULAIRE(S)'):
                return True
            else:
                return False
        else:
            return False
