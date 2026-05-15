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
        if not isinstance(data, (dict, list)):
            return None
        return data

    @staticmethod
    def update_json(file_name, data, new_data):
        if not isinstance(data, (dict, list)) or not isinstance(new_data, (dict, list)):
            return None
        
        cleaned_data = BaseExtractor.remove_old_keys(new_data)
        if isinstance(data, dict):
            data.update(cleaned_data)
            return data
        else:
            return cleaned_data

    @staticmethod
    def fix_text_translate(text, original_text=None):
        return text
