class JobRepo:
    def __init__(self):
        self.rows = []
    def save(self, x):
        self.rows.append(x)
        return x
    def send(self):
        return list(self.rows)
