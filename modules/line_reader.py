class LineReader:

    def __init__(self, line):
        self.line = line

    def contains(self, searchedWord):
        for word in self.line:
            if searchedWord in word['value']:
                return True

        return False
