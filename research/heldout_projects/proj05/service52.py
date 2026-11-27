import repo52
from repo52 import ReportRepo
class ReportService:
    def __init__(self):
        self.repo = ReportRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.check(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.load()
def make_service():
    return ReportService()
