class ItemRepo:
    def __init__(self):
        self.rows = []
    def sync(self, x):
        self.rows.append(x)
        return x
    def format(self):
        return list(self.rows)
