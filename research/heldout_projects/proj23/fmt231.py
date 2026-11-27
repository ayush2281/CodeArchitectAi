class EventFmt0:
    def render(self, x):
        return str(x)
class MessageFmt1:
    def render(self, x):
        return str(x)
class UserFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'eventfmt0': EventFmt0, 'messagefmt1': MessageFmt1, 'userfmt2': UserFmt2}
    return table[key]()
