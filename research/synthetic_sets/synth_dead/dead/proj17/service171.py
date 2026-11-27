import repo171
from repo171 import CartRepo
class CartService:
    def __init__(self):
        self.repo = CartRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.build(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.merge()
def make_service():
    return CartService()
