class ReportRepo:
    def __init__(self):
        self.rows = []
    def check(self, x):
        self.rows.append(x)
        return x
    def load(self):
        return list(self.rows)
