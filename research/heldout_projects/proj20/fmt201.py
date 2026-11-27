class InvoiceFmt0:
    def render(self, x):
        return str(x)
class MessageFmt1:
    def render(self, x):
        return str(x)
class TicketFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'invoicefmt0': InvoiceFmt0, 'messagefmt1': MessageFmt1, 'ticketfmt2': TicketFmt2}
    return table[key]()
