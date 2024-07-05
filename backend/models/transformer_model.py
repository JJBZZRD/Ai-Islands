import importlib

# TODO: create the associated methods referenced from the controler class. 

class TransformerModel:
    def __init__(self, class_names, model_name=None):
        self.classes = self._import_classes(class_names)
        self.model = self._initialize_model(model_name) if model_name else None

    def _import_classes(self, class_names):
        imported_classes = {}
        for class_name in class_names:
            module_name, class_name = class_name.rsplit('.', 1)
            module = importlib.import_module(module_name)
            imported_classes[class_name] = getattr(module, class_name)
        return imported_classes

    def _initialize_model(self, model_name):
        if model_name not in self.classes:
            raise ValueError(f"Model name '{model_name}' not found in imported classes.")
        return self.classes[model_name]()
