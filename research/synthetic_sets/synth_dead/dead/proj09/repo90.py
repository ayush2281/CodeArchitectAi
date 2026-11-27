class TaskRepo:
    def __init__(self):
        self.rows = []
    def sync(self, x):
        self.rows.append(x)
        return x
    def render(self):
        return list(self.rows)
