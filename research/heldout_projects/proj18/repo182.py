class ItemRepo:
    def __init__(self):
        self.rows = []
    def save(self, x):
        self.rows.append(x)
        return x
    def sync(self):
        return list(self.rows)
