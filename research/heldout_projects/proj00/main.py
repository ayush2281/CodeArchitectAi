import events00
events00.dispatch('save0', 1)
events00.dispatch('format1', 1)
events00.dispatch('send2', 1)
import strat01
strat01.Context(strat01.send_strategy0).execute(1)
strat01.Context(strat01.merge_strategy1).execute(1)
import model02
a = model02.Order.from_text('abc')
b = model02.Order(2)
(a + b)()
a.double
