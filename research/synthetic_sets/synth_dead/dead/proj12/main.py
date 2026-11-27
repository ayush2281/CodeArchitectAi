import shapes120
import func121
import extra12

def main():
    for c in [shapes120.Order0, shapes120.Invoice1, shapes120.Ticket2, shapes120.Account3]:
        c().run()
    func121.apply_all([1, 2, 3])
    extra12.call_by_name_12('hook_12', 1)

main()
