import repo272
from repo272 import TaskRepo
class TaskService:
    def __init__(self):
        self.repo = TaskRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.check(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.build()
def make_service():
    return TaskService()
