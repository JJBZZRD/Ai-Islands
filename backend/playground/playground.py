class Playground:
    def __init__(self, playground_id: str, playground_info: dict):
        self.playground_id = playground_id
        self.description = playground_info.get("description", "")
        self.models = playground_info.get("models", {})
        self.chain = playground_info.get("chain", [])
        self.active_chain = False

    def create_playground_dictionary(self):
        return {
            "description": self.description,
            "models": self.models,
            "chain": self.chain,
            "active_chain": self.active_chain
        }
