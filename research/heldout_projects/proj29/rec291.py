def fact(n):
    return 1 if n <= 1 else n * fact(n - 1)

def even(n):
    return True if n == 0 else odd(n - 1)

def odd(n):
    return False if n == 0 else even(n - 1)

def counter():
    c = [0]
    def inc():
        c[0] += 1
        return bump(c[0])
    return inc

def bump(v):
    return v
