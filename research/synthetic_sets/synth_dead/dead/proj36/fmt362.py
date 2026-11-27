class OrderFmt0:
    def render(self, x):
        return str(x)
class MessageFmt1:
    def render(self, x):
        return str(x)
class ReportFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'orderfmt0': OrderFmt0, 'messagefmt1': MessageFmt1, 'reportfmt2': ReportFmt2}
    return table[key]()
