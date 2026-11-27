import strat250
import fmt251
import events252
import extra25

def main():
    strat250.Context(strat250.format_strategy0).execute(1)
    strat250.Context(strat250.audit_strategy1).execute(1)
    fmt251.get_formatter('invoicefmt0').render(1)
    fmt251.get_formatter('messagefmt1').render(1)
    events252.dispatch('parse0', 1)
    events252.dispatch('sync1', 1)
    events252.dispatch('update2', 1)
    extra25.call_by_name_25('hook_25', 1)

main()
