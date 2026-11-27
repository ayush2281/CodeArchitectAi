import repo182
from repo182 import ItemRepo
class ItemService:
    def __init__(self):
        self.repo = ItemRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.save(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.sync()
def make_service():
    return ItemService()
