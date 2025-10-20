import csv
import os
from extractor.BaseExtractor import BaseExtractor
import commun.TextsUtils as TextsUtils


class CSVExtractor(BaseExtractor):
    name = 'CSV'
    files_types = ['csv']

    def __init__(self, translate):
        super().__init__(translate)
        self.columns_to_translate = ['value', 'text']
        self.csv_delimiter = ','
        self.skip_empty = True
        self.skip_headers = True

    @classmethod
    def get_interactive_questions(cls):
        return [
            {
                'key': 'columns',
                'question': 'Digite os nomes das colunas a traduzir (separadas por vírgula, ex: value,text):',
                'title': '\n=== CONFIGURAÇÃO CSV ===',
                'description': 'Especifique quais colunas do CSV devem ser traduzidas.',
                'color': 'cyan',
                'required': False
            },
            {
                'key': 'delimiter',
                'question': 'Digite o delimitador do CSV (padrão: vírgula):',
                'description': 'Exemplo: , (vírgula), ; (ponto e vírgula), \\t (tab)',
                'color': 'yellow',
                'required': False
            }
        ]

    def apply_configuration(self, config):
        if 'columns' in config and config['columns']:
            columns = [col.strip() for col in config['columns'].split(',')]
            self.columns_to_translate = columns
            print(f"✓ Colunas configuradas para tradução: {', '.join(columns)}")
        else:
            print(f"⚠ Usando colunas padrão: {', '.join(self.columns_to_translate)}")

        if 'delimiter' in config and config['delimiter']:
            delimiter = config['delimiter']
            if delimiter == '\\t':
                delimiter = '\t'
            elif delimiter == '\\n':
                delimiter = '\n'
            self.csv_delimiter = delimiter
            print(f"✓ Delimitador configurado: '{delimiter}'")

    @classmethod
    def extract_files(cls, file_path):
        if not file_path.endswith(tuple(cls.files_types)):
            return [os.path.basename(file_path), None]

        try:
            with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                return [os.path.basename(file_path), data]
        except Exception as e:
            print(f"Erro ao ler CSV {file_path}: {e}")
            return [os.path.basename(file_path), None]

    def extract_text(self, file_name, data):
        if not data:
            return None

        texts_to_translate = {}

        for row_idx, row in enumerate(data):
            for column in self.columns_to_translate:
                if column in row:
                    text = row[column]

                    if self.skip_empty and not text:
                        continue

                    if self.skip_headers and text.startswith('■'):
                        continue

                    key = f"row_{row_idx}_col_{column}"
                    texts_to_translate[key] = text

        return texts_to_translate if texts_to_translate else None

    def update_json(self, file_name, data, new_data):
        if not data or not new_data:
            return data

        updated_data = []

        for row_idx, row in enumerate(data):
            updated_row = row.copy()

            for column in self.columns_to_translate:
                if column in row:
                    key = f"row_{row_idx}_col_{column}"

                    if key in new_data:
                        if row[column] and row[column] != new_data[key]:
                            updated_row[f"{column}_old"] = row[column]

                        updated_row[column] = new_data[key]

            updated_data.append(updated_row)

        return updated_data

    @staticmethod
    def import_file(file_name, data, folder):
        if not data:
            return

        file_path = os.path.join(folder, file_name)

        try:
            if isinstance(data, list) and len(data) > 0:
                fieldnames = list(data[0].keys())

                seen = set(fieldnames)
                for row in data:
                    for key in row.keys():
                        if key not in seen:
                            fieldnames.append(key)
                            seen.add(key)
            else:
                return

            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(data)

        except Exception as e:
            print(f"Erro ao salvar CSV {file_name}: {e}")

    @staticmethod
    def fix_text_translate(text):
        if isinstance(text, dict):
            for key, value in text.items():
                if isinstance(value, str):
                    text[key] = value.strip()
        return text
