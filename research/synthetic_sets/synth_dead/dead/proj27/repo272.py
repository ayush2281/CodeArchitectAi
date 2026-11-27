class TaskRepo:
    def __init__(self):
        self.rows = []
    def check(self, x):
        self.rows.append(x)
        return x
    def build(self):
        return list(self.rows)
