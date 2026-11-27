import events290
events290.dispatch('build0', 1)
events290.dispatch('format1', 1)
events290.dispatch('audit2', 1)
import rec291
rec291.fact(3)
rec291.even(4)
rec291.counter()()
import model292
a = model292.Cart.from_text('abc')
b = model292.Cart(2)
(a + b)()
a.double
