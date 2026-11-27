import rec360
rec360.fact(3)
rec360.even(4)
rec360.counter()()
import events361
events361.dispatch('check0', 1)
events361.dispatch('merge1', 1)
events361.dispatch('build2', 1)
import model362
a = model362.Invoice.from_text('abc')
b = model362.Invoice(2)
(a + b)()
a.double
