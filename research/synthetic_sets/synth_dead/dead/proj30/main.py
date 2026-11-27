import util300
from util300 import extra
import shapes301
import extra30

def main():
    util300.message_savex(1)
    extra.combo(2)
    for c in [shapes301.Invoice0, shapes301.Invoice1]:
        c().run()
    extra30.call_by_name_30('hook_30', 1)

main()
