import service320
import mix321
import extra32

def main():
    s = service320.make_service()
    s.create(320)
    s.create(320+1)
    s.listing()
    mix321.Model().run()
    extra32.call_by_name_32('hook_32', 1)

main()
