import repo321
from repo321 import ReportRepo
class ReportService:
    def __init__(self):
        self.repo = ReportRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.check(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.audit()
def make_service():
    return ReportService()
