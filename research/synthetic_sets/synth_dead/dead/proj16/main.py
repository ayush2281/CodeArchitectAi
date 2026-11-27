import fmt160
import func161
import util162
from util162 import extra
import extra16

def main():
    fmt160.get_formatter('userfmt0').render(1)
    fmt160.get_formatter('orderfmt1').render(1)
    func161.apply_all([1, 2, 3])
    util162.report_syncx(1)
    extra.combo(2)
    extra16.call_by_name_16('hook_16', 1)

main()
