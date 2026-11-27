import service360
import model361
import fmt362
import extra36

def main():
    s = service360.make_service()
    s.create(360)
    s.create(360+1)
    s.listing()
    a = model361.Order.from_text('abc')
    b = model361.Order(2)
    (a + b)()
    a.double
    fmt362.get_formatter('orderfmt0').render(1)
    fmt362.get_formatter('messagefmt1').render(1)
    extra36.call_by_name_36('hook_36', 1)

main()
