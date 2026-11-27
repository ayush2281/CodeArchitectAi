import res100
import fmt101
import extra10

def main():
    res100.consume()
    fmt101.get_formatter('jobfmt0').render(1)
    fmt101.get_formatter('invoicefmt1').render(1)
    extra10.call_by_name_10('hook_10', 1)

main()
