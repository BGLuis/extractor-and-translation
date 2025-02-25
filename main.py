import extractor
from translate import Translate
import os
import glob
import threading
from datetime import datetime
import time

def process_file(file, retries=3, delay=20):
    translate = Translate()
    for attempt in range(retries):
        try:
            data = extractor.extract_files(file)
            temp = extractor.extract_text(data[0], data[1])
            if temp:
                temp = translate.translator(temp)
                extractor.import_files(data[0], temp, 'process')
                print(f"File {file} processed successfully")
            return
        except Exception as e:
            print(f"Error processing file {file}")
            if attempt < retries - 1:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"Failed to process file {file} after {retries} attempts")

if __name__ == '__main__':
    start_time = datetime.now()
    print("Start :", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    folderProcess = 'process'
    folderInput = 'input'
    folderOutput = 'output'

    threads = []

    for file in glob.glob(folderProcess+'/*'):
        os.remove(file)
    for file in glob.glob(folderOutput+'/*'):
        os.remove(file)

    for file in glob.glob(folderInput + '/*'):
        print("Processing file: ", file)
        thread = threading.Thread(target=process_file, args=(file,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    for file in glob.glob(folderProcess + '/*'):
        print(file)
        file_name = os.path.basename(file)
        input_file = os.path.join(folderInput, file_name)
        if os.path.exists(input_file):
            process_data = extractor.extract_files(file)
            input_data = extractor.extract_files(input_file)
            updated_data = extractor.update_json(file_name, input_data[1], process_data[1])
            extractor.import_files(file_name, updated_data, folderOutput)

    Translate.save_cache()
    end_time = datetime.now()
    print("Current time:", end_time.strftime("%Y-%m-%d %H:%M:%S"))
    print("Time taken:", end_time - start_time)