import repo20
from repo20 import JobRepo
class JobService:
    def __init__(self):
        self.repo = JobRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.parse(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.load()
def make_service():
    return JobService()
