class TaskFmt0:
    def render(self, x):
        return str(x)
class AccountFmt1:
    def render(self, x):
        return str(x)
class CartFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'taskfmt0': TaskFmt0, 'accountfmt1': AccountFmt1, 'cartfmt2': CartFmt2}
    return table[key]()
