import model70
import deco71
import extra7

def main():
    a = model70.Job.from_text('abc')
    b = model70.Job(2)
    (a + b)()
    a.double
    deco71.pipeline(1)
    extra7.call_by_name_7('hook_7', 1)

main()
