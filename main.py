from datetime import datetime
from translate.GoogleTranslate import GoogleTranslate
from extractor.RPGMakerExtractor import RPGMakerExtractor
from extractor.BaseExtractor import BaseExtractor
from translate.BaseTranslate import BaseTranslate
import cli

lang_options = {
    'portugues': 'pt',
    'ingles': 'en',
    'espanhol': 'es',
    'frances': 'fr',
    'italiano': 'it',
    'japones': 'ja',
    'automatico': 'auto'
}

def list_subclasses(cls):
    cls = cls.__subclasses__()
    subclasses = []
    for subclass in cls:
        subclasses.append((subclass.name, subclass))
    return subclasses

def list_subclasses_extractor():
    cls = BaseExtractor.__subclasses__()
    subclasses = {}
    for subclass in cls:
        subclasses[subclass.name] = subclass
    return subclasses

def list_subclasses_translate():
    cls = BaseTranslate.__subclasses__()
    subclasses = {}
    for subclass in cls:
        subclasses[subclass.agent] = subclass
    return subclasses

def remove_lang_options(lang_source):
    for key in lang_options.keys():
        if lang_options[key] == lang_source:
            lang_options.pop(key)
            break
    lang_options.pop('automatico')


if __name__ == '__main__':
    extractor = cli.select_opition("Que Tipo de extrator de Texto vc gostaria:", list_subclasses_extractor())
    translator = cli.select_opition("Que Tipo de agente de tradução vc gostaria:", list_subclasses_translate())
    translate = translator()

    lang_source = cli.select_opition("Selecione o idioma de origem:", lang_options)
    remove_lang_options(lang_source)
    lang_target = cli.select_opition("Selecione o idioma de destino:", lang_options)

    translate.change_language(lang_source, lang_target)

    extractor = extractor(translate)
    extractor.init_folder()

    cli.instruction(f"Trasfira os arquivos para a pasta '{extractor.folderInput}', e pressione enter tecla para continuar")
    extractor.process_files()
    cli.show_status(extractor.threads_status)

    cli.instruction(f"Verifique a tradução dos arquivos na pasta '{extractor.folderProcess}', e pressione enter tecla para continuar")

    cli.print_colored_line("Exportando arquivos", 'green')
    extractor.import_files()

    translate.save_cache()
    cli.print_colored_line("Tradução finalizada \nPressione enter tecla para continuar")
