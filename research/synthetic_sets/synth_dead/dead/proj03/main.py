import service30
import model31
import func32
import extra3

def main():
    s = service30.make_service()
    s.create(30)
    s.create(30+1)
    s.listing()
    a = model31.Account.from_text('abc')
    b = model31.Account(2)
    (a + b)()
    a.double
    func32.apply_all([1, 2, 3])
    extra3.call_by_name_3('hook_3', 1)

main()
