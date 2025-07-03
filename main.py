from translate import *
from extractor import *
from extractor.BaseExtractor import BaseExtractor
from translate.BaseTranslate import BaseTranslate
import shutil
import cli
import os

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
    if lang_source != 'auto':
        lang_options.pop('automatico')

def copy_file(src, dst):
    shutil.copy(src, dst)

def copy_folder(src, dst):
    shutil.copytree(src, dst)

def delete_file_folder(pasta):
    for arquivo in os.listdir(pasta):
        caminho = os.path.join(pasta, arquivo)
        if os.path.isfile(caminho):
            os.remove(caminho)

def copy_files_only(src, dst):
    if not os.path.exists(dst):
        os.makedirs(dst)

    delete_file_folder(dst)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)


if __name__ == '__main__':
    extractor = cli.select_opition("Que Tipo de extrator de Texto vc gostaria:", list_subclasses_extractor())
    translator = cli.select_opition("Que Tipo de agente de tradução vc gostaria:", list_subclasses_translate())
    translate = translator()

    lang_source = cli.select_opition("Selecione o idioma de origem:", lang_options)
    remove_lang_options(lang_source)
    lang_target = cli.select_opition("Selecione o idioma de destino:", lang_options)

    translate.change_language(lang_source, lang_target)

    cli.clear_screen()
    extractor = extractor(translate)
    extractor.init_folder()

    # cli.instruction(f"Trasfira os arquivos para a pasta '{extractor.folderInput}', e pressione enter tecla para continuar")
    cli.instruction(f"Precione enter para selecionar a pasta de entrada dos arquivos")
    dir = cli.select_folder("Selecione a pasta de entrada dos arquivos")
    if dir is None:
        cli.print_colored_line("Nenhuma pasta selecionada. Encerrando o programa.", 'red')
        exit(1)
    copy_files_only(dir, dir+"-"+lang_source)
    copy_files_only(dir, extractor.folderInput)
    extractor.process_files()
    cli.show_status(extractor.threads_status)

    cli.instruction(f"Verifique a tradução dos arquivos na pasta '{extractor.folderProcess}', e pressione enter tecla para continuar")

    cli.print_colored_line("Exportando arquivos", 'green')
    extractor.import_files()
    copy_files_only(extractor.folderOutput, dir)

    translate.save_cache()
    cli.print_colored_line("Tradução finalizada \nPressione enter tecla para continuar")
