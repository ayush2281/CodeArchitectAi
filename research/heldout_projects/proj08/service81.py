import repo81
from repo81 import InvoiceRepo
class InvoiceService:
    def __init__(self):
        self.repo = InvoiceRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.check(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.sync()
def make_service():
    return InvoiceService()
