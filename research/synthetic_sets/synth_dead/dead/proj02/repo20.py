class JobRepo:
    def __init__(self):
        self.rows = []
    def parse(self, x):
        self.rows.append(x)
        return x
    def load(self):
        return list(self.rows)
