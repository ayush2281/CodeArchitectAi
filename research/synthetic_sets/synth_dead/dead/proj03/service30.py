import repo30
from repo30 import AccountRepo
class AccountService:
    def __init__(self):
        self.repo = AccountRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.check(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.save()
def make_service():
    return AccountService()
