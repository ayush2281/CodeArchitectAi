import events270
events270.dispatch('render0', 1)
events270.dispatch('send1', 1)
events270.dispatch('send2', 1)
import res271
res271.consume()
import fmt272
fmt272.get_formatter('orderfmt0').render(1)
fmt272.get_formatter('eventfmt1').render(1)
