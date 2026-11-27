def legacy_9(x):
    return x + 1

def old_helper_9(x):
    return legacy_9(x)

class Unused9:
    def never_9(self):
        return 0

HOOKS_9 = {}

def hook_9(x):
    return x

def call_by_name_9(name, x):
    return globals()[name](x)
