class TicketFmt0:
    def render(self, x):
        return str(x)
class OrderFmt1:
    def render(self, x):
        return str(x)
class CartFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'ticketfmt0': TicketFmt0, 'orderfmt1': OrderFmt1, 'cartfmt2': CartFmt2}
    return table[key]()
