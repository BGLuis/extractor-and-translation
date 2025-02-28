from datetime import datetime
from translate.GoogleTranslate import GoogleTranslate
from extractor.RPGMakerExtractor import RPGMakerExtractor

if __name__ == '__main__':
    start_time = datetime.now()
    print("Start :", start_time.strftime("%Y-%m-%d %H:%M:%S"))

    translate = GoogleTranslate()
    extractor = RPGMakerExtractor(translate)

    extractor.init_folder()
    extractor.process_files()
    extractor.import_files()

    GoogleTranslate.save_cache()
    end_time = datetime.now()
    print("Current time:", end_time.strftime("%Y-%m-%d %H:%M:%S"))
    print("Time taken:", end_time - start_time)