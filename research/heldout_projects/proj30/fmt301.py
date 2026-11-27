class AccountFmt0:
    def render(self, x):
        return str(x)
class TicketFmt1:
    def render(self, x):
        return str(x)
class TaskFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'accountfmt0': AccountFmt0, 'ticketfmt1': TicketFmt1, 'taskfmt2': TaskFmt2}
    return table[key]()
