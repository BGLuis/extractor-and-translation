import re

class RPGTextFilters:
    IGNORE_PREFIXES = [
        "$", "D_TEXT", "\"+", "\'+", "voice_", "ChoiceVariableId", "PLM", "\"00",
        "let result", "const ", "var ", "this.", "return", "if", "else", "while", "for", "function", "=>",
        "new ", "class ", "extends ", "super(", "import ", "export ", "async ", "await ",
        "try", "catch", "finally", "false", "true", "null", "undefined", "NaN",
    ]

    IGNORE_PARAMS = [
        "&&", "||", "==", "!=", "===", "!==", "$gamevariables.value", "Math."
    ]

    TECHNICAL_VALUES = {
        'YES', 'NO', 'OK', 'CANCEL', 'TRUE', 'FALSE', 'NULL', 'UNDEFINED',
        'END', 'START', 'STOP', 'PLAY', 'PAUSE', 'NOCHANNEL', 'CHANNEL',
        'LEFT', 'RIGHT', 'CENTER', 'TOP', 'BOTTOM', 'MIDDLE', 'ON', 'OFF',
        'NO CHANGE', 'NONE', 'AUTO', 'DEFAULT', 'ALWAYS', 'NEVER',
        'ENABLE', 'DISABLE', 'ENABLED', 'DISABLED',
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'
    }

    @staticmethod
    def is_numeric(text):
        if not isinstance(text, str): return False
        try:
            float(text.replace(',', '.'))
            return True
        except ValueError:
            return False

    @staticmethod
    def is_boolean(text):
        if not isinstance(text, str): return False
        return text.lower() in ['true', 'false']

    @staticmethod
    def is_technical_or_code(text):
        if not isinstance(text, str):
            if isinstance(text, list):
                return all(RPGTextFilters.is_technical_or_code(item) for item in text)
            return True # Retornamos True (ignorar) se não for string nem lista (ex: int, float, bool)

        if text == '':
            return True

        if text.upper() in RPGTextFilters.TECHNICAL_VALUES:
            return True

        # Ignorar apenas números
        clean_text = text.replace('.', '').replace(',', '').replace('-', '').replace('+', '').replace(' ', '')
        if clean_text.isdigit():
            return True

        if any(text.startswith(prefix) for prefix in RPGTextFilters.IGNORE_PREFIXES):
            return True

        if any(param in text for param in RPGTextFilters.IGNORE_PARAMS):
            return True

        return False
