import repo320
from repo320 import JobRepo
class JobService:
    def __init__(self):
        self.repo = JobRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.save(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.send()
def make_service():
    return JobService()
