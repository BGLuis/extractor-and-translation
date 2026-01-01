import re
import threading
from abc import ABC, abstractmethod
import copy
import glob
import json
import os
import time
import logging
import commun.TextsUtils as TextsUtils

logging.basicConfig(filename='error.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(message)s')

class BaseExtractor(ABC):
    name = 'BaseExtractor'
    folderProcess = 'process'
    folderInput = 'input'
    folderOutput = 'output'
    threads = []
    files_types = []

    def __init__(self, translate):
        self.create_directory_if_not_exists(self.__class__.folderProcess)
        self.create_directory_if_not_exists(self.__class__.folderInput)
        self.create_directory_if_not_exists(self.__class__.folderOutput)
        self.translate = translate
        self.threads_status = []
        # Removido o semáforo: a paralelização agora é controlada internamente
        # por translate_batch_parallel usando ThreadPoolExecutor
        # self.semaphore = threading.Semaphore(translate.MAX_REQUESTS_SIMULTANEOUSLY)

    @staticmethod
    def create_directory_if_not_exists(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def clean_folder(folder):
        for file in glob.glob(folder + '/*'):
            os.remove(file)

    @classmethod
    def extract_files(cls, file_path):
        if not file_path.endswith(tuple(cls.files_types)):
            return [os.path.basename(file_path), None]
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [os.path.basename(file_path), data]

    @staticmethod
    def init_folder():
        BaseExtractor.clean_folder(BaseExtractor.folderProcess)
        BaseExtractor.clean_folder(BaseExtractor.folderOutput)

    @classmethod
    def get_interactive_questions(cls):
        return []

    def apply_configuration(self, config):
        pass

    @staticmethod
    @abstractmethod
    def extract_text(file_name, data):
        pass

    @staticmethod
    @abstractmethod
    def update_json(file_name, data, new_data):
        pass

    @staticmethod
    def import_file(file_name, json_data, folder):
        with open(os.path.join(folder, file_name), 'w', encoding='utf-8') as f:
            f.write(json.dumps(json_data, ensure_ascii=False, separators=(',', ':')))

    @staticmethod
    @abstractmethod
    def fix_text_translate(text, original_text=None):
        pass

    @staticmethod
    def remove_old_keys(obj):
        if isinstance(obj, dict):
            return {k: BaseExtractor.remove_old_keys(v) for k, v in obj.items() if not k.endswith('_old')}
        elif isinstance(obj, list):
            return [BaseExtractor.remove_old_keys(i) for i in obj]
        else:
            return obj

    @staticmethod
    def merge_dicts_texts(dict1, dict2):
        merged_dict = dict2.copy()
        haystack = dict1.items() if isinstance(dict1, dict) else enumerate(dict1)
        for key, value in haystack:
            if isinstance(value, str):
                if key in merged_dict and merged_dict[key] != value:
                    merged_dict[f"{key}_old"] = merged_dict[key]
                    # merged_dict[f"{key}_old_char_count"] = len(merged_dict[key])
                merged_dict[key] = value
            elif isinstance(value, dict):
                merged_dict[key] = BaseExtractor.merge_dicts_texts(value, merged_dict[key])
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict) or isinstance(item, list):
                        merged_dict[key][i] = BaseExtractor.merge_dicts_texts(value[i], merged_dict[key][i])
                    else:
                        if key in merged_dict and merged_dict[key][i] != item:
                            if f"{key}_old" not in merged_dict:
                                merged_dict[f"{key}_old"] = []
                                merged_dict[f"{key}_old_char_count"] = []
                            merged_dict[f"{key}_old"].append(merged_dict[key][i])
                            # merged_dict[f"{key}_old_char_count"].append(len(merged_dict[key][i]))
                        merged_dict[key][i] = item
        return merged_dict

    def add_threads_status(self, status):
        for i, s in enumerate(self.threads_status):
            if s['file'] == status['file']:
                self.threads_status.remove(s)
        self.threads_status.append(status)

    def process_file(self, file, retries=6, delay=20):
        # Removido o bloqueio de semáforo aqui - cada arquivo processa livremente
        # O controle de requisições simultâneas agora está dentro de translate_batch_parallel
        translate = copy.deepcopy(self.translate)
        for attempt in range(retries):
            try:
                file_name, data = self.extract_files(file)
                temp = self.extract_text(file_name, data)
                # Antes de traduzir: mascarar tokens técnicos para evitar que o tradutor
                # altere variáveis, códigos e formatações. Usamos padrões genéricos;
                # extractors específicos podem fornecer padrões mais restritos.
                # Selecionar padrões de mascaramento: preferir padrões fornecidos pelo
                # extractor (método get_mask_patterns ou atributo mask_patterns).
                # Caso contrário, usar padrões genéricos que cobrem tokens comuns.
                if temp:
                    try:
                        if hasattr(self, 'get_mask_patterns') and callable(getattr(self, 'get_mask_patterns')):
                            patterns = self.get_mask_patterns(file_name, data)
                        elif hasattr(self, 'mask_patterns'):
                            patterns = self.mask_patterns
                        else:
                            patterns = [
                                re.compile(r'\\[A-Za-z]{1,3}\s*\[[^\]]*\]', re.IGNORECASE),
                                re.compile(r'\$game[a-zA-Z_]+\b', re.IGNORECASE),
                                re.compile(r'\$\s*[a-z]+[A-Z][a-zA-Z]*'),
                                re.compile(r'!?(?<!\\)\b[A-Za-z]{1,2}\s*\[\s*\d+\s*\]', re.IGNORECASE),
                            ]

                        # Garantir que `patterns` seja uma lista de regex compilados
                        if isinstance(patterns, (list, tuple)):
                            compiled_patterns = []
                            for p in patterns:
                                if isinstance(p, str):
                                    compiled_patterns.append(re.compile(p))
                                else:
                                    compiled_patterns.append(p)
                            patterns = compiled_patterns
                        else:
                            patterns = [patterns]

                        try:
                            masked_temp, _mask_map = TextsUtils.mask_tokens_in_structure(temp, patterns, prefix="__XTOK_")
                        except Exception:
                            masked_temp, _mask_map = temp, {}
                    except Exception:
                        masked_temp, _mask_map = temp, {}
                else:
                    masked_temp, _mask_map = temp, {}
                if temp:
                    old = copy.deepcopy(temp)
                    self.add_threads_status({'file': file, 'status': 'process', 'msg': "Processing file"})

                    def progress_callback(current, total):
                        self.add_threads_status({
                            'file': file,
                            'status': 'process',
                            'current': current,
                            'total': total,
                            'msg': f"Translating batch {current}/{total}"
                        })

                    # Chamar tradutor com a versão mascarada
                    translate.translator(masked_temp, progress_callback)

                    # Após tradução, restaurar os tokens originais
                    try:
                        if _mask_map:
                            unmasked = TextsUtils.unmask_tokens_in_structure(masked_temp, _mask_map)
                        else:
                            unmasked = masked_temp
                    except Exception:
                        unmasked = masked_temp

                    # Aplicar correções (fix_text_translate) APENAS nos dados extraídos/traduzidos
                    # Isso evita corromper a estrutura do JSON original ou scripts não extraídos
                    try:
                        self.fix_text_translate(unmasked, old)
                    except Exception as e:
                        logging.error(f"Error applying fix_text_translate in process_file: {e}")

                    merge = self.merge_dicts_texts(unmasked, old)

                    updated_data = self.update_json(file_name, data, merge)
                    self.import_file(file_name, updated_data, self.folderProcess)
                    self.add_threads_status({'file': file, 'status': 'success', 'msg': "Processed successfully"})
                else:
                    self.add_threads_status(
                        {'file': file, 'status': 'ignore', 'msg': "No text to process"})
                    self.import_file(file_name, data, self.folderOutput)

                return
            except Exception as e:
                logging.error(f"Error processing file {file}: {e}")
                self.add_threads_status(
                    {'file': file, 'status': 'danger', 'msg': f"Error processing file {file}"})
                if attempt < retries - 1:
                    self.add_threads_status(
                        {'file': file, 'status': 'waiting', 'msg': f"Retrying in {delay} seconds..."})
                    time.sleep(delay)
                    translate.reduce_limite()
                else:
                    self.add_threads_status(
                        {'file': file, 'status': 'erro', 'msg': f"Failed to process after {retries}"})

    def process_files(self):
        for file in glob.glob(self.__class__.folderInput + '/*'):
            thread = threading.Thread(target=self.process_file, args=(file,))
            self.threads.append(thread)
            thread.start()

    def import_files(self):
        for thread in self.threads:
            thread.join()

        for file in glob.glob(self.__class__.folderProcess + '/*'):
            file_name = os.path.basename(file)
            input_file = os.path.join(BaseExtractor.folderInput, file_name)
            if os.path.exists(input_file):
                # Carregar dados do arquivo processado (traduzido)
                process_data = self.extract_files(file)

                # Carregar dados do arquivo original para comparação
                original_data = self.extract_files(input_file)
                original_json = original_data[1] if original_data[1] else None

                # Log para debug
                if original_json is None:
                    logging.warning(f"⚠️ fix_text_translate called WITHOUT original JSON for {file_name}")

                # Corrigir texto traduzido usando o original JSON como referência
                # Passamos o JSON completo (process_data[1]) e o JSON original (original_json)
                # self.fix_text_translate(process_data[1], original_json)

                self.import_file(file_name, process_data[1], BaseExtractor.folderOutput)

        # Após importar todos os arquivos, aplicar sanitização final nos arquivos gerados
        # try:
        #    self.sanitize_output_files()
        # except Exception as e:
        #    logging.error(f"Error during sanitize_output_files: {e}")

    def sanitize_output_files(self):
        """
        Varre os arquivos JSON em `folderOutput` e remove números com zeros à esquerda
        que aparecem em trechos de código (podem se tornar literais octais em JS strict).

        Heurística:
        - Percorre todos os valores string dentro do JSON.
        - Para cada string que contém padrões parecidos com código (if(, var , function, =>, mes =, text =)
          substitui tokens numéricos com zeros à esquerda por sua forma sem zeros.
        - Não altera números que estão dentro de literais de string (detectado por contagem de aspas simples/duplas).
        """
        import json
        import re
        from pathlib import Path

        code_triggers = ['if(', 'var ', 'return', '=>', 'function', 'mes =', 'text =']
        num_leading_zero = re.compile(r"\b0+([0-9]+)\b")

        for p in Path(self.folderOutput).glob('*.json'):
            try:
                data = json.load(p.open('r', encoding='utf-8'))
            except Exception:
                continue

            changed = False

            def walk(obj):
                nonlocal changed
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        obj[k] = walk(v)
                    return obj
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        obj[i] = walk(v)
                    return obj
                elif isinstance(obj, str):
                    s = obj
                    if any(t in s for t in code_triggers) and num_leading_zero.search(s):
                        # substituir apenas ocorrências que não estejam dentro de aspas
                        def repl(m):
                            start, end = m.start(), m.end()
                            # heurística: se número estiver dentro de aspas na string, não substituir
                            before = s[:start]
                            after = s[end:]
                            in_double = before.count('"') % 2 == 1 and after.count('"') % 2 == 1
                            in_single = before.count("'") % 2 == 1 and after.count("'") % 2 == 1
                            if in_double or in_single:
                                return m.group(0)
                            else:
                                changed_local = True
                                return m.group(1)

                        new_s = num_leading_zero.sub(repl, s)
                        if new_s != s:
                            changed = True
                            return new_s
                    return s
                else:
                    return obj

            new_data = walk(data)
            if changed:
                try:
                    with p.open('w', encoding='utf-8') as fh:
                        json.dump(new_data, fh, ensure_ascii=False, separators=(',', ':'))
                except Exception as e:
                    logging.error(f"Failed to write sanitized file {p}: {e}")
