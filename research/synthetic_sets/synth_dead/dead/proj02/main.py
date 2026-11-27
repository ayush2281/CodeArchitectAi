import service20
import res21
import util22
from util22 import extra
import extra2

def main():
    s = service20.make_service()
    s.create(20)
    s.create(20+1)
    s.listing()
    res21.consume()
    util22.account_savex(1)
    extra.combo(2)
    extra2.call_by_name_2('hook_2', 1)

main()
