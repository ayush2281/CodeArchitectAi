import repo380
from repo380 import OrderRepo
class OrderService:
    def __init__(self):
        self.repo = OrderRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.update(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.send()
def make_service():
    return OrderService()
