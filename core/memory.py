class Memory:
    def __init__(self, max_history=20):
        self.history = []
        self.max_history = max_history

    def add_user(self, text):
        self.history.append({"role": "user", "content": text})
        self._trim()

    def add_jarvis(self, text):
        self.history.append({"role": "assistant", "content": text})
        self._trim()

    def get(self):
        return self.history

    def clear(self):
        self.history = []

    def _trim(self):
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
