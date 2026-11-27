class OrderRepo:
    def __init__(self):
        self.rows = []
    def update(self, x):
        self.rows.append(x)
        return x
    def send(self):
        return list(self.rows)
