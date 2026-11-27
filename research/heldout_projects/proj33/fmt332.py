class EventFmt0:
    def render(self, x):
        return str(x)
class ReportFmt1:
    def render(self, x):
        return str(x)
class MessageFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'eventfmt0': EventFmt0, 'reportfmt1': ReportFmt1, 'messagefmt2': MessageFmt2}
    return table[key]()
