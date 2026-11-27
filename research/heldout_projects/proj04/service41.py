import repo41
from repo41 import ItemRepo
class ItemService:
    def __init__(self):
        self.repo = ItemRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.sync(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.format()
def make_service():
    return ItemService()
