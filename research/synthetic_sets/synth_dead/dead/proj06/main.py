import events60
import res61
import util62
from util62 import extra
import extra6

def main():
    events60.dispatch('send0', 1)
    events60.dispatch('format1', 1)
    events60.dispatch('build2', 1)
    res61.consume()
    util62.message_syncx(1)
    extra.combo(2)
    extra6.call_by_name_6('hook_6', 1)

main()
