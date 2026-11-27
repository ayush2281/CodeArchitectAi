import repo370
from repo370 import TicketRepo
class TicketService:
    def __init__(self):
        self.repo = TicketRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.audit(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.update()
def make_service():
    return TicketService()
