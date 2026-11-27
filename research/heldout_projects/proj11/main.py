import res110
res110.consume()
import events111
events111.dispatch('send0', 1)
events111.dispatch('check1', 1)
events111.dispatch('sync2', 1)
import model112
a = model112.Report.from_text('abc')
b = model112.Report(2)
(a + b)()
a.double
