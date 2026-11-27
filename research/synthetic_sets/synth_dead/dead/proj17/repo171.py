class CartRepo:
    def __init__(self):
        self.rows = []
    def build(self, x):
        self.rows.append(x)
        return x
    def merge(self):
        return list(self.rows)
