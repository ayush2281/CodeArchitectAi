import rec310
import events311
import extra31

def main():
    rec310.fact(3)
    rec310.even(4)
    rec310.counter()()
    events311.dispatch('sync0', 1)
    events311.dispatch('merge1', 1)
    events311.dispatch('send2', 1)
    extra31.call_by_name_31('hook_31', 1)

main()
