class OrderFmt0:
    def render(self, x):
        return str(x)
class EventFmt1:
    def render(self, x):
        return str(x)
class UserFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'orderfmt0': OrderFmt0, 'eventfmt1': EventFmt1, 'userfmt2': UserFmt2}
    return table[key]()
