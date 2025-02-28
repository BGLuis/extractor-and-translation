class IntWrapper:
    def __init__(self, value):
        self.value = value
    def add(self, value):
        self.value += value
    def get(self):
        return self.value