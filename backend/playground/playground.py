class Playground:
    """
    The Playground class represents a playground environment where models can be added, configured, and executed in a chain.

    Attributes:
        playground_id (str): The unique identifier for the playground.
        description (str): A description of the playground.
        models (dict): A dictionary of models added to the playground.
        chain (list): A list representing the order of models to be executed.
        active_chain (bool): A flag indicating whether the chain is currently active.
    """

    def __init__(
        self,
        playground_id: str,
        description: str = "",
        models: dict = {},
        chain: list = [],
    ):
        """
        Initializes a new instance of the Playground class.

        Args:
            playground_id (str): The unique identifier for the playground.
            description (str, optional): A description of the playground. Defaults to an empty string.
            models (dict, optional): A dictionary of models added to the playground. Defaults to an empty dictionary.
            chain (list, optional): A list representing the chain of models to be executed. Defaults to an empty list.
        """
        self.playground_id = playground_id
        self.description = description
        self.models = models
        self.chain = chain
        self.active_chain = False

    def create_playground_dictionary(self):
        """
        Creates a dictionary representation of the playground.

        Returns:
            dict: A dictionary containing the playground's description, models, chain, and active chain status.
        """
        return {
            "description": self.description,
            "models": self.models,
            "chain": self.chain,
            "active_chain": self.active_chain,
        }
