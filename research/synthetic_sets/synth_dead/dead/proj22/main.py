import service220
import shapes221
import model222
import extra22

def main():
    s = service220.make_service()
    s.create(220)
    s.create(220+1)
    s.listing()
    for c in [shapes221.Order0, shapes221.Report1, shapes221.Account2, shapes221.Ticket3]:
        c().run()
    a = model222.Item.from_text('abc')
    b = model222.Item(2)
    (a + b)()
    a.double
    extra22.call_by_name_22('hook_22', 1)

main()
