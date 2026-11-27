import service200
s = service200.make_service()
s.create(200)
s.create(200+1)
s.listing()
import fmt201
fmt201.get_formatter('invoicefmt0').render(1)
fmt201.get_formatter('messagefmt1').render(1)
import res202
res202.consume()
