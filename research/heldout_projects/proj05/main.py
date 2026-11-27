import fmt50
fmt50.get_formatter('cartfmt0').render(1)
fmt50.get_formatter('accountfmt1').render(1)
import events51
events51.dispatch('update0', 1)
events51.dispatch('sync1', 1)
events51.dispatch('merge2', 1)
import service52
s = service52.make_service()
s.create(52)
s.create(52+1)
s.listing()
