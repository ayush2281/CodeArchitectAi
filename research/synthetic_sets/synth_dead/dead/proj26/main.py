import mix260
import model261
import extra26

def main():
    mix260.Model().run()
    a = model261.Item.from_text('abc')
    b = model261.Item(2)
    (a + b)()
    a.double
    extra26.call_by_name_26('hook_26', 1)

main()
