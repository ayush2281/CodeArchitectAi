import repo90
from repo90 import TaskRepo
class TaskService:
    def __init__(self):
        self.repo = TaskRepo()
    def create(self, x):
        self.validate(x)
        return self.repo.sync(x)
    def validate(self, x):
        return bool(x)
    def listing(self):
        return self.repo.render()
def make_service():
    return TaskService()
