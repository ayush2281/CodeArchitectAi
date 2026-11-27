import repo130
from repo130 import ReportRepo
class ReportService:
    def __init__(self):
        self.repo = ReportRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.render(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.update()
def make_service():
    return ReportService()
