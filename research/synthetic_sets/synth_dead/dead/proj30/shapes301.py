class ReportBase:
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
class Invoice0(ReportBase):
    def step(self):
        return self.helper() + 0
    def helper(self):
        return 0
class Invoice1(ReportBase):
    def step(self):
        return self.helper() + 1
    def helper(self):
        return 1
    def finish(self, r):
        return super().finish(r) + 1
