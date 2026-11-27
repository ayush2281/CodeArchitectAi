class CartFmt0:
    def render(self, x):
        return str(x)
class AccountFmt1:
    def render(self, x):
        return str(x)
class EventFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'cartfmt0': CartFmt0, 'accountfmt1': AccountFmt1, 'eventfmt2': EventFmt2}
    return table[key]()
