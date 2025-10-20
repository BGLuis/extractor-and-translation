from extractor.BaseExtractor import BaseExtractor
class JsonExtractor(BaseExtractor):
    name = 'Json'
    files_types = ['json']

    @classmethod
    def get_interactive_questions(cls):
        return []

    def apply_configuration(self, config):
        pass

    def __init__(self, translate):
        super().__init__(translate)

    @staticmethod
    def extract_text(file_name, data):
        if not isinstance(data, dict):
            return None
        return data

    @staticmethod
    def update_json(file_name, data, new_data):
        if not isinstance(data, dict) or not isinstance(new_data, dict):
            return None
        data.update(JsonExtractor.remove_old_keys(new_data))
        return data

    @staticmethod
    def fix_text_translate(text):
        return text
