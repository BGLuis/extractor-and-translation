import re
import threading
from abc import ABC, abstractmethod
import copy
import glob
import json
import os
import time


class BaseExtractor(ABC):
    name = 'BaseExtractor'
    folderProcess = 'process'
    folderInput = 'input'
    folderOutput = 'output'
    threads = []

    def __init__(self, translate):
        self.create_directory_if_not_exists(self.folderProcess)
        self.create_directory_if_not_exists(self.folderInput)
        self.create_directory_if_not_exists(self.folderOutput)
        self.translate = translate
        self.threads_status = []
        self.semaphore = threading.Semaphore(translate.MAX_REQUESTS_SIMULTANEOUSLY)


    @staticmethod
    def create_directory_if_not_exists(directory):
        if not os.path.exists(directory):
            os.makedirs(directory)


    @staticmethod
    def clean_folder(folder):
        for file in glob.glob(folder+'/*'):
            os.remove(file)


    @staticmethod
    def extract_files(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
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
        with open(os.path.join(folder, file_name), 'w', encoding='utf-8') as f:
            f.write(json.dumps(json_data, ensure_ascii=False, indent=4))


    @staticmethod
    @abstractmethod
    def fix_text_translate(text):
        pass


    def add_threads_status(self, status):
        for i, s in enumerate(self.threads_status):
            if s['file'] == status['file']:
                self.threads_status.remove(s)
        self.threads_status.append(status)


    def process_file(self, file, retries=5, delay=20):
        with self.semaphore:
            translate = copy.deepcopy(self.translate)
            for attempt in range(retries):
                try:
                    data = self.extract_files(file)
                    temp = self.extract_text(data[0], data[1])
                    if temp:
                        self.add_threads_status({'file': file, 'status': 'process', 'msg': "Processing file"})
                        temp = translate.translator(temp)
                        self.import_file(data[0], temp, self.folderProcess)
                        self.add_threads_status({'file': file, 'status': 'success', 'msg': "Processed successfully"})
                    else:
                        self.add_threads_status(
                            {'file': file, 'status': 'ignore', 'msg': "No text to process"})
                        self.import_file(data[0], data[1], self.folderOutput)

                    return
                except Exception as e:
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
        for file in glob.glob(self.folderInput + '/*'):
            thread = threading.Thread(target=self.process_file, args=(file,))
            self.threads.append(thread)
            thread.start()


    def import_files(self):
        for thread in self.threads:
            thread.join()

        for file in glob.glob(self.folderProcess + '/*'):
            file_name = os.path.basename(file)
            input_file = os.path.join(BaseExtractor.folderInput, file_name)
            if os.path.exists(input_file):
                process_data = self.extract_files(file)
                input_data = self.extract_files(input_file)
                self.fix_text_translate(process_data[1])
                updated_data = self.update_json(file_name, input_data[1], process_data[1])
                self.import_file(file_name, updated_data, BaseExtractor.folderOutput)