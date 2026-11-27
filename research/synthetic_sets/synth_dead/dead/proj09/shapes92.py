class TaskBase:
    def run(self):
        self.prepare()
        r = self.step()
        return self.finish(r)
    def prepare(self):
        return 1
    def step(self):
        return 0
    def finish(self, r):
        return r
class Item0(TaskBase):
    def step(self):
        return self.helper() + 0
    def helper(self):
        return 0
class Item1(TaskBase):
    def step(self):
        return self.helper() + 1
    def helper(self):
        return 1
    def finish(self, r):
        return super().finish(r) + 1
class Account2(TaskBase):
    def step(self):
        return self.helper() + 2
    def helper(self):
        return 2
class Ticket3(TaskBase):
    def step(self):
        return self.helper() + 3
    def helper(self):
        return 3
    def finish(self, r):
        return super().finish(r) + 1
