class UserFmt0:
    def render(self, x):
        return str(x)
class OrderFmt1:
    def render(self, x):
        return str(x)
class CartFmt2:
    def render(self, x):
        return str(x)
def get_formatter(key):
    table = {'userfmt0': UserFmt0, 'orderfmt1': OrderFmt1, 'cartfmt2': CartFmt2}
    return table[key]()
