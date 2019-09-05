import sys
sys.path.append('./modules')
from linereader import LineReader

class CCMParser:

    def __init__(self, lines):
        self.lines = lines
        self.currentAccount = None
        self.data = []

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
