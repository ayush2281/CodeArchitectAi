class OrderFmt0:
    def render(self, x):
        return str(x)
class TicketFmt1:
    def render(self, x):
        return str(x)
class EventFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'orderfmt0': OrderFmt0, 'ticketfmt1': TicketFmt1, 'eventfmt2': EventFmt2}
    return table[key]()
