import res40
res40.consume()
import service41
s = service41.make_service()
s.create(41)
s.create(41+1)
s.listing()
import model42
a = model42.Ticket.from_text('abc')
b = model42.Ticket(2)
(a + b)()
a.double
