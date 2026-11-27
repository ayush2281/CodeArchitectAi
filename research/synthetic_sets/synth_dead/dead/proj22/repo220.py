class EventRepo:
    def __init__(self):
        self.rows = []
    def build(self, x):
        self.rows.append(x)
        return x
    def save(self):
        return list(self.rows)
