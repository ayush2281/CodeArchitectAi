import model200
import func201
import extra20

def main():
    a = model200.User.from_text('abc')
    b = model200.User(2)
    (a + b)()
    a.double
    func201.apply_all([1, 2, 3])
    extra20.call_by_name_20('hook_20', 1)

main()
