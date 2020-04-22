class LineReader:

    def __init__(self, line):
        # Todo check if line is properly formatted
        self.line = line

    def contains(self, searchedWord):
        for word in self.line:
            if searchedWord in word['value']:
                return True

        return False
