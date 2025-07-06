import re
import threading
from abc import ABC, abstractmethod
import copy
import glob
import json
import os
import time
import logging

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
        self.semaphore = threading.Semaphore(translate.MAX_REQUESTS_SIMULTANEOUSLY)

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
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            return [os.path.basename(file_path), data]

    @staticmethod
    def init_folder():
        BaseExtractor.clean_folder(BaseExtractor.folderProcess)
        BaseExtractor.clean_folder(BaseExtractor.folderOutput)

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
        with open(os.path.join(folder, file_name), 'w', encoding='utf-8-sig') as f:
            f.write(json.dumps(json_data, ensure_ascii=False, indent=4))

    @staticmethod
    @abstractmethod
    def fix_text_translate(text):
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
        with self.semaphore:
            translate = copy.deepcopy(self.translate)
            for attempt in range(retries):
                try:
                    file_name, data = self.extract_files(file)
                    temp = self.extract_text(file_name, data)
                    if temp:
                        old = copy.deepcopy(temp)
                        self.add_threads_status({'file': file, 'status': 'process', 'msg': "Processing file"})
                        translate.translator(temp)
                        merge = self.merge_dicts_texts(temp, old)

                        self.import_file(file_name, merge, self.folderProcess)
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
                process_data = self.extract_files(file)
                input_data = self.extract_files(input_file)
                self.fix_text_translate(process_data[1])
                updated_data = self.update_json(file_name, input_data[1], process_data[1])
                self.import_file(file_name, updated_data, BaseExtractor.folderOutput)
