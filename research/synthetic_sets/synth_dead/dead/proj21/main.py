import shapes210
import deco211
import rec212
import extra21

def main():
    for c in [shapes210.User0, shapes210.Cart1]:
        c().run()
    deco211.pipeline(1)
    rec212.fact(3)
    rec212.even(4)
    rec212.counter()()
    extra21.call_by_name_21('hook_21', 1)

main()
