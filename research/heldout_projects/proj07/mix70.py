class LogMixin:
    def log(self, m):
        return m

class SaveMixin:
    def save(self):
        return self.log('save')

class Model(LogMixin, SaveMixin):
    def __init__(self):
        super().__init__()
    def run(self):
        self.log('run')
        return self.save()
