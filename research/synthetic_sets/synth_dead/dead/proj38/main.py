import rec380
import events381
import shapes382
import extra38

def main():
    rec380.fact(3)
    rec380.even(4)
    rec380.counter()()
    events381.dispatch('check0', 1)
    events381.dispatch('render1', 1)
    events381.dispatch('send2', 1)
    for c in [shapes382.Event0, shapes382.User1]:
        c().run()
    extra38.call_by_name_38('hook_38', 1)

main()
