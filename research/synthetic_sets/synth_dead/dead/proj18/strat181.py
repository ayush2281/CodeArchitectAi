def render_strategy0(x):
    return x + 0
def build_strategy1(x):
    return x + 1
def update_strategy2(x):
    return x + 2
class Context:
    def __init__(self, strategy):
        self.strategy = strategy
    def execute(self, x):
        return self.strategy(x)
