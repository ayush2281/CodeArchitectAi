class JobFmt0:
    def render(self, x):
        return str(x)
class InvoiceFmt1:
    def render(self, x):
        return str(x)
class ReportFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'jobfmt0': JobFmt0, 'invoicefmt1': InvoiceFmt1, 'reportfmt2': ReportFmt2}
    return table[key]()
