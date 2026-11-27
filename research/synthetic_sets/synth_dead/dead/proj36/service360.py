import repo360
from repo360 import CartRepo
class CartService:
    def __init__(self):
        self.repo = CartRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.format(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.check()
def make_service():
    return CartService()
