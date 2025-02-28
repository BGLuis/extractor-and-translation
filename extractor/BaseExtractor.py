import re
import threading
from abc import ABC, abstractmethod
import copy
import glob
import json
import os
import time

class BaseExtractor(ABC):
    folderProcess = 'process'
    folderInput = 'input'
    folderOutput = 'output'
    threads = []

    def __init__(self, translate):
        self.create_directory_if_not_exists(self.folderProcess)
        self.create_directory_if_not_exists(self.folderInput)
        self.create_directory_if_not_exists(self.folderOutput)
        self.translate = translate


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


    def process_file(self, file, retries=5, delay=20):
        translate = copy.deepcopy(self.translate)
        for attempt in range(retries):
            try:
                data = self.extract_files(file)
                temp = self.extract_text(data[0], data[1])
                if temp:
                    temp = translate.translator(temp)
                    self.import_file(data[0], temp, 'process')
                    print(f"File {file} processed successfully")
                return
            except Exception as e:
                print(f"Error processing file {file}")
                if attempt < retries - 1:
                    print(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    translate.reduce_limite()
                else:
                    print(f"Failed to process file {file} after {retries} attempts")


    def process_files(self):
        for file in glob.glob(self.folderInput + '/*'):
            print("Processing file: ", file)
            thread = threading.Thread(target=self.process_file, args=(file,))
            self.threads.append(thread)
            thread.start()


    def import_files(self):
        for thread in self.threads:
            thread.join()

        for file in glob.glob(self.folderProcess + '/*'):
            print(file)
            file_name = os.path.basename(file)
            input_file = os.path.join(BaseExtractor.folderInput, file_name)
            if os.path.exists(input_file):
                process_data = self.extract_files(file)
                input_data = self.extract_files(input_file)
                BaseExtractor.fix_text_translate(input_data)
                updated_data = self.update_json(file_name, input_data[1], process_data[1])
                self.import_file(file_name, updated_data, BaseExtractor.folderOutput)