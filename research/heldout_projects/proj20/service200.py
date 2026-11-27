import repo200
from repo200 import ItemRepo
class ItemService:
    def __init__(self):
        self.repo = ItemRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.audit(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.parse()
def make_service():
    return ItemService()
