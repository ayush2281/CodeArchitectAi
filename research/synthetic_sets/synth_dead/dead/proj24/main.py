import strat240
import events241
import fmt242
import extra24

def main():
    strat240.Context(strat240.send_strategy0).execute(1)
    strat240.Context(strat240.send_strategy1).execute(1)
    events241.dispatch('render0', 1)
    events241.dispatch('audit1', 1)
    events241.dispatch('check2', 1)
    fmt242.get_formatter('orderfmt0').render(1)
    fmt242.get_formatter('ticketfmt1').render(1)
    extra24.call_by_name_24('hook_24', 1)

main()
