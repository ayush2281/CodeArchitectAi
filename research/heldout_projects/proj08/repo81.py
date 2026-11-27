class InvoiceRepo:
    def __init__(self):
        self.rows = []
    def check(self, x):
        self.rows.append(x)
        return x
    def sync(self):
        return list(self.rows)
