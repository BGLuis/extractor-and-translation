# src/factory.py

_EXTRACTORS = {}
_TRANSLATORS = {}

def register_extractor(name, hidden=False, **kwargs):
    """
    Decorator para registrar um Extrator.
    :param name: Nome que aparecerá na CLI/GUI.
    :param hidden: Se True, não aparecerá na lista de opções.
    :param kwargs: Quaisquer propriedades extras a serem injetadas na classe.
    """
    def decorator(cls):
        if not hidden:
            _EXTRACTORS[name] = cls
            cls.name = name  # Força o nome na classe para manter compatibilidade
            for key, value in kwargs.items():
                setattr(cls, key, value)
        return cls
    return decorator

def register_translator(name, hidden=False, **kwargs):
    """
    Decorator para registrar um Tradutor.
    :param name: Nome que aparecerá na CLI/GUI.
    :param hidden: Se True, não aparecerá na lista de opções.
    :param kwargs: Quaisquer propriedades extras a serem injetadas na classe.
    """
    def decorator(cls):
        if not hidden:
            _TRANSLATORS[name] = cls
            cls.agent = name # Força o agent na classe para manter compatibilidade
            for key, value in kwargs.items():
                setattr(cls, key, value)
        return cls
    return decorator

class ExtractorFactory:
    @staticmethod
    def get_available():
        return _EXTRACTORS.copy()

    @staticmethod
    def create(extractor_name, translate_instance):
        extractors = ExtractorFactory.get_available()
        if extractor_name in extractors:
            return extractors[extractor_name](translate_instance)
        raise ValueError(f"Extrator '{extractor_name}' não suportado.")

class TranslatorFactory:
    @staticmethod
    def get_available():
        return _TRANSLATORS.copy()

    @staticmethod
    def create(translator_name):
        translators = TranslatorFactory.get_available()
        if translator_name in translators:
            return translators[translator_name]()
        raise ValueError(f"Tradutor '{translator_name}' não suportado.")
