import service90
import events91
import shapes92
import extra9

def main():
    s = service90.make_service()
    s.create(90)
    s.create(90+1)
    s.listing()
    events91.dispatch('check0', 1)
    events91.dispatch('load1', 1)
    events91.dispatch('send2', 1)
    for c in [shapes92.Item0, shapes92.Item1, shapes92.Account2, shapes92.Ticket3]:
        c().run()
    extra9.call_by_name_9('hook_9', 1)

main()
