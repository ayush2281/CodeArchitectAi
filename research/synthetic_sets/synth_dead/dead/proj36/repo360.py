class CartRepo:
    def __init__(self):
        self.rows = []
    def format(self, x):
        self.rows.append(x)
        return x
    def check(self):
        return list(self.rows)
