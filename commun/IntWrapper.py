class IntWrapper:
    def __init__(self, value):
        self.value = value

    def add(self, value):
        self.value += value

    def get(self):
        return self.value

    def __repr__(self):
        return f"IntWrapper({self.value})"

    def __str__(self):
        return str(self.value)
