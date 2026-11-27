class JobFmt0:
    def render(self, x):
        return str(x)
class UserFmt1:
    def render(self, x):
        return str(x)
class EventFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'jobfmt0': JobFmt0, 'userfmt1': UserFmt1, 'eventfmt2': EventFmt2}
    return table[key]()
