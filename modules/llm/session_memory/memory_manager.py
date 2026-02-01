from .storage_json import load_memory, save_memory

class SessionMemory:
    def __init__(self, user_id="default"):
        self.user_id = user_id
        self.memory = load_memory(user_id)

    def get(self, key, default=None):
        return self.memory.get(key, default)

    def set(self, key, value):
        self.memory[key] = value
        save_memory(self.user_id, self.memory)

    def delete(self, key):
        if key in self.memory:
            del self.memory[key]
            save_memory(self.user_id, self.memory)

    def clear(self):
        self.memory = {}
        save_memory(self.user_id, self.memory)
