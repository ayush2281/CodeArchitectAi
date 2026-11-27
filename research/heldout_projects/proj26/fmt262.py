class JobFmt0:
    def render(self, x):
        return str(x)
class JobFmt1:
    def render(self, x):
        return str(x)
class EventFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'jobfmt0': JobFmt0, 'jobfmt1': JobFmt1, 'eventfmt2': EventFmt2}
    return table[key]()
