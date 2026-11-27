class Resource:
    def __enter__(self):
        self.open()
        return self
    def __exit__(self, *a):
        self.close()
    def open(self):
        return 1
    def close(self):
        return 0

def stream(n):
    for i in range(n):
        yield transform(i)

def transform(i):
    return i + 1

def consume():
    with Resource() as r:
        return sum(stream(3))
