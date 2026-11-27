class Ticket:
    def __init__(self, v):
        self.v = v
    @classmethod
    def from_text(cls, t):
        return cls(cls.parse(t))
    @staticmethod
    def parse(t):
        return len(t)
    @property
    def double(self):
        return self.scale(2)
    def scale(self, f):
        return self.v * f
    def __add__(self, o):
        return Ticket(self.v + o.v)
    def __call__(self):
        return self.scale(1)
