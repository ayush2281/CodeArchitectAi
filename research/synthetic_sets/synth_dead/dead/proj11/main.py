import events110
import deco111
import extra11

def main():
    events110.dispatch('sync0', 1)
    events110.dispatch('merge1', 1)
    events110.dispatch('update2', 1)
    deco111.pipeline(1)
    extra11.call_by_name_11('hook_11', 1)

main()
