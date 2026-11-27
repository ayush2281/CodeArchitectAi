import repo220
from repo220 import EventRepo
class EventService:
    def __init__(self):
        self.repo = EventRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.build(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.save()
def make_service():
    return EventService()
