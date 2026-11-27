class TicketRepo:
    def __init__(self):
        self.rows = []
    def audit(self, x):
        self.rows.append(x)
        return x
    def update(self):
        return list(self.rows)
