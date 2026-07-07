from src.services.FileNameTranslator import FileNameTranslator
import shutil
from src import cli
import os
import argparse
import sys
import time
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler('processamento.log', maxBytes=5*1024*1024, backupCount=2, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

lang_options = {
    'Português': 'pt',
    'Inglês': 'en',
    'Espanhol': 'es',
    'Francês': 'fr',
    'Italiano': 'it',
    'Japonês': 'ja',
    'Automático (Detectar)': 'auto'
}

from src.factory import ExtractorFactory, TranslatorFactory

def remove_lang_options(lang_source):
    """Remove o idioma de origem e a opção 'auto' da lista de destino"""
    # Remove o idioma selecionado como origem
    for key in list(lang_options.keys()):
        if lang_options[key] == lang_source:
            lang_options.pop(key)
            break
            
    # Se a origem não for auto, remove o auto do destino
    if lang_source != 'auto':
        auto_keys = [k for k, v in lang_options.items() if v == 'auto']
        for k in auto_keys:
            lang_options.pop(k)

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
    src_real = os.path.realpath(src)
    dst_real = os.path.realpath(dst)

    # Evita apagar os arquivos quando origem e destino apontam para a mesma pasta.
    if src_real == dst_real:
        return

    if not os.path.exists(dst):
        os.makedirs(dst)

    delete_file_folder(dst)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isfile(s):
            shutil.copy2(s, d)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Sistema de extração e tradução de textos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py --gui
  python main.py --interactive
  python main.py -e RPGMaker -t Google -s pt -d en -i /path/to/input
  python main.py --extractor JsonExtractor --translator Ollama --source ja --target pt --input ./data --no-backup
  python main.py --list-extractors
  python main.py --list-translators
        """
    )

    parser.add_argument('-g', '--gui', action='store_true',
                       help='Iniciar interface gráfica (PyQt5)')
    parser.add_argument('-e', '--extractor',
                       help='Tipo de extrator (use --list-extractors para ver opções)')
    parser.add_argument('-t', '--translator',
                       help='Tipo de tradutor (use --list-translators para ver opções)')
    parser.add_argument('-s', '--source',
                       help='Idioma de origem (pt, en, es, fr, it, ja, auto)')
    parser.add_argument('-d', '--target',
                       help='Idioma de destino (pt, en, es, fr, it, ja)')
    parser.add_argument('-i', '--input',
                       help='Pasta de entrada dos arquivos')
    parser.add_argument('--synopsis', '--sinopse',
                       help='Sinopse do jogo para melhorar contexto da tradução')

    parser.add_argument('--no-backup', action='store_true',
                       help='Não criar backup dos arquivos originais')
    parser.add_argument('--no-verify', action='store_true',
                       help='Não pausar para verificação manual dos arquivos processados')
    parser.add_argument('--interactive', action='store_true',
                       help='Modo interativo (padrão se nenhum argumento for fornecido)')

    parser.add_argument('--mode', choices=['content', 'filenames'], default='content',
                       help='Modo de operação: traduzir conteúdo de arquivos (content) ou nomes de arquivos (filenames)')
    parser.add_argument('--keep-original', action='store_true',
                       help='No modo filenames, manter o arquivo original e criar uma cópia traduzida')

    parser.add_argument('--list-extractors', action='store_true',
                       help='Listar extratores disponíveis')
    parser.add_argument('--list-translators', action='store_true',
                       help='Listar tradutores disponíveis')
    parser.add_argument('--list-languages', action='store_true',
                       help='Listar idiomas suportados')

    return parser.parse_args()


def list_options():
    """Print available options and exit"""
    print("\n=== EXTRATORES DISPONÍVEIS ===")
    extractors = ExtractorFactory.get_available()
    for name in extractors.keys():
        print(f"  - {name}")

    print("\n=== TRADUTORES DISPONÍVEIS ===")
    translators = TranslatorFactory.get_available()
    for name in translators.keys():
        print(f"  - {name}")

    print("\n=== IDIOMAS SUPORTADOS ===")
    for lang_name, lang_code in lang_options.items():
        print(f"  - {lang_code}: {lang_name}")


def validate_arguments(args):
    errors = []

    if args.extractor:
        extractors = ExtractorFactory.get_available()
        if args.extractor not in extractors:
            errors.append(f"Extrator '{args.extractor}' não encontrado. Opções: {list(extractors.keys())}")

    if args.translator:
        translators = TranslatorFactory.get_available()
        if args.translator not in translators:
            errors.append(f"Tradutor '{args.translator}' não encontrado. Opções: {list(translators.keys())}")

    if args.source and args.source not in lang_options.values():
        errors.append(f"Idioma de origem '{args.source}' não suportado. Opções: {list(lang_options.values())}")

    if args.target and args.target not in lang_options.values():
        errors.append(f"Idioma de destino '{args.target}' não suportado. Opções: {list(lang_options.values())}")

    if args.input and not os.path.exists(args.input):
        errors.append(f"Pasta de entrada '{args.input}' não existe")

    if args.source and args.target and args.source == args.target:
        errors.append("Idioma de origem e destino não podem ser iguais")

    return errors


def run_filename_translation_workflow(args, translators):
    """Fluxo de trabalho para tradução de nomes de arquivos"""
    # 1. Selecionar Tradutor
    if args.translator and args.translator in translators:
        translator_class = translators[args.translator]
    else:
        translator_class = cli.select_option("Selecione o tradutor:", translators)
        if translator_class == "Exit": return False

    translate = TranslatorFactory.create(translator_class.agent)

    # 2. Selecionar Idioma de Origem
    if args.source and args.source in lang_options.values():
        lang_source = args.source
    else:
        lang_source = cli.select_option("Selecione o idioma de origem:", lang_options)
        if lang_source == "Exit": return False

    remove_lang_options(lang_source)

    # 3. Selecionar Idioma de Destino
    if args.target and args.target in lang_options.values():
        lang_target = args.target
    else:
        lang_target = cli.select_option("Selecione o idioma de destino:", lang_options)
        if lang_target == "Exit": return False

    translate.change_language(lang_source, lang_target)

    # 4. Configuração do Tradutor
    if args.synopsis:
        translate.apply_configuration({'synopsis': args.synopsis})
    else:
        translator_questions = translator_class.get_interactive_questions()
        if translator_questions:
            cli.clear_screen()
            translator_config = {}
            for question in translator_questions:
                if 'title' in question: cli.print_colored_line(question['title'], 'cyan')
                cli.print_colored_line(question['question'], question.get('color', 'white'))
                answer = input().strip()
                if answer or not question.get('required', False):
                    translator_config[question['key']] = answer
            translate.apply_configuration(translator_config)

    # 5. Opção de Salvar (Apenas tradução ou Ambos)
    keep_original = args.keep_original
    if not args.keep_original and not args.translator: # Se não foi passado via CLI
        save_options = {
            'Salvar apenas a tradução (Renomear/Copiar com novo nome)': False,
            'Salvar os dois juntos (Manter original e criar cópia traduzida)': True
        }
        keep_original = cli.select_option("Como deseja salvar os arquivos?", save_options)
        if keep_original == "Exit": return False

    # 6. Selecionar Pasta de Entrada
    if args.input and os.path.exists(args.input):
        input_dir = args.input
    else:
        input_dir = input("\nDigite o caminho da pasta com os arquivos (ou pressione Enter para './input'): ").strip()
        if not input_dir:
            input_dir = 'input'
        
        if not os.path.exists(input_dir):
            cli.print_colored_line(f"Pasta '{input_dir}' não encontrada.", 'red')
            return False

    # 7. Executar Tradução
    fn_translator = FileNameTranslator(translate)
    fn_translator.process_directory(input_dir, keep_original)
    return True


def run_workflow(args):
    """
    Fluxo de trabalho unificado que usa argumentos CLI se fornecidos,
    caso contrário, solicita ao usuário de forma interativa.
    """
    extractors = ExtractorFactory.get_available()
    translators = TranslatorFactory.get_available()

    # Selecionar Modo de Operação
    mode = args.mode
    if mode == 'content' and not any([args.extractor, args.translator, args.input, args.gui]):
        # Se nenhum argumento relevante foi passado, pergunta o modo
        modes = {
            'Extrair e Traduzir Conteúdo de Arquivos': 'content',
            'Traduzir Nomes de Arquivos': 'filenames',
            'Sair': 'Exit'
        }
        mode = cli.select_option("O que você deseja fazer?", modes)
        if mode == "Exit": return False

    if mode == 'filenames':
        return run_filename_translation_workflow(args, translators)

    # 1. Selecionar Extrator
    if args.extractor and args.extractor in extractors:
        extractor_class = extractors[args.extractor]
    else:
        extractor_class = cli.select_option("Selecione o extrator de texto:", extractors)
        if extractor_class == "Exit": return False

    # 2. Selecionar Tradutor
    if args.translator and args.translator in translators:
        translator_class = translators[args.translator]
    else:
        translator_class = cli.select_option("Selecione o tradutor:", translators)
        if translator_class == "Exit": return False

    translate = TranslatorFactory.create(translator_class.agent)

    # 3. Selecionar Idioma de Origem
    if args.source and args.source in lang_options.values():
        lang_source = args.source
    else:
        lang_source = cli.select_option("Selecione o idioma de origem:", lang_options)
        if lang_source == "Exit": return False

    remove_lang_options(lang_source)

    # 4. Selecionar Idioma de Destino
    if args.target and args.target in lang_options.values():
        lang_target = args.target
    else:
        lang_target = cli.select_option("Selecione o idioma de destino:", lang_options)
        if lang_target == "Exit": return False

    translate.change_language(lang_source, lang_target)

    # 5. Configuração do Tradutor
    if args.synopsis:
        translate.apply_configuration({'synopsis': args.synopsis})
        cli.print_colored_line(f"✓ Sinopse configurada via CLI", 'green')
    else:
        translator_questions = translator_class.get_interactive_questions()
        if translator_questions:
            cli.clear_screen()
            translator_config = {}
            for question in translator_questions:
                if 'title' in question: cli.print_colored_line(question['title'], 'cyan')
                if 'description' in question: cli.print_colored_line(question['description'], question.get('color', 'yellow'))
                cli.print_colored_line(question['question'], question.get('color', 'white'))
                answer = input().strip()
                if answer or not question.get('required', False):
                    translator_config[question['key']] = answer
                else:
                    cli.print_colored_line(f"\n✗ {question['key'].capitalize()} é obrigatório!", 'red')
                    return False
            translate.apply_configuration(translator_config)

    # 6. Configuração do Extrator
    extractor = ExtractorFactory.create(extractor_class.name, translate)
    extractor_questions = extractor.get_interactive_questions()
    if extractor_questions:
        cli.clear_screen()
        extractor_config = {}
        for question in extractor_questions:
            if 'title' in question: cli.print_colored_line(question['title'], 'cyan')
            if 'description' in question: cli.print_colored_line(question['description'], question.get('color', 'yellow'))
            cli.print_colored_line(question['question'], question.get('color', 'white'))
            answer = input().strip()
            if answer or not question.get('required', False):
                extractor_config[question['key']] = answer
            else:
                cli.print_colored_line(f"\n✗ {question['key'].capitalize()} é obrigatório!", 'red')
                return False
        extractor.apply_configuration(extractor_config)

    extractor.init_folder()

    # 7. Selecionar Pasta de Entrada
    if args.input and os.path.exists(args.input):
        input_dir = args.input
    else:
        cli.instruction(f"Pressione enter para selecionar a pasta de entrada dos arquivos")
        input_dir = cli.select_folder("Selecione a pasta de entrada dos arquivos")
        if input_dir is None:
            cli.print_colored_line("Nenhuma pasta selecionada. Encerrando o programa.", 'red')
            return False

    # 8. Executar Processo
    cli.clear_screen()
    cli.print_colored_line(f"Usando extrator: {extractor_class.name}", 'cyan')
    cli.print_colored_line(f"Usando tradutor: {translator_class.agent}", 'cyan')
    cli.print_colored_line(f"Traduzindo de {lang_source} para {lang_target}", 'cyan')
    cli.print_colored_line(f"Pasta de entrada: {input_dir}", 'cyan')

    return run_extraction_process(
        extractor, translate, input_dir, lang_source, 
        backup=not args.no_backup, 
        verify=not args.no_verify
    )


def run_extraction_process(extractor, translate, input_dir, lang_source, backup=True, verify=True, gui_signals=None):
    """Run the main extraction and translation process"""
    def log(msg, color='white'):
        logging.info(msg)
        if gui_signals:
            gui_signals.log.emit(msg, color)
        else:
            cli.print_colored_line(msg, color)

    try:
        if backup:
            backup_dir = input_dir + "-" + lang_source
            log(f"Criando backup em: {backup_dir}", 'yellow')
            copy_files_only(input_dir, backup_dir)

        copy_files_only(input_dir, extractor.folderInput)

        log("Iniciando processamento dos arquivos...", 'green')
        extractor.process_files()
        
        if not gui_signals:
            cli.show_status(extractor.threads_status)

        if verify:
            if gui_signals:
                log(f"Aviso: Verificação manual simplificada no modo GUI. Verifique a pasta '{extractor.folderProcess}'.", 'yellow')
            else:
                cli.instruction(f"Verifique a tradução dos arquivos na pasta '{extractor.folderProcess}', e pressione enter tecla para continuar")

        log("Exportando arquivos", 'green')
        extractor.import_files()
        copy_files_only(extractor.folderOutput, input_dir)

        translate.save_cache()
        log("Tradução finalizada com sucesso!", 'green')

        return True

    except Exception as e:
        log(f"Erro durante o processamento: {str(e)}", 'red')
        return False


if __name__ == '__main__':
    setup_logging()
    args = parse_arguments()

    # Opção para iniciar GUI
    if args.gui:
        try:
            from src.gui import run_gui
            run_gui(args, lang_options, run_extraction_process)
            sys.exit(0)
        except ImportError as e:
            cli.print_colored_line(f"Erro: Não foi possível carregar a interface gráfica. Verifique se o PyQt5 está instalado.", 'red')
            cli.print_colored_line(f"Detalhes: {e}", 'yellow')
            cli.print_colored_line("\nIniciando modo terminal em 3 segundos...", 'cyan')
            time.sleep(3)

    # Opções de listagem
    if args.list_extractors or args.list_translators or args.list_languages:
        list_options()
        sys.exit(0)

    # Validar argumentos se fornecidos via CLI
    if any([args.extractor, args.translator, args.source, args.target, args.input]):
        errors = validate_arguments(args)
        if errors:
            cli.print_colored_line("Erros nos argumentos CLI:", 'red')
            for error in errors:
                cli.print_colored_line(f"  - {error}", 'red')
            cli.print_colored_line("\nIniciando modo interativo para corrigir...", 'yellow')
            time.sleep(2)
            # Limpar argumentos inválidos para forçar prompt
            extractors = ExtractorFactory.get_available()
            translators = TranslatorFactory.get_available()
            if args.extractor not in extractors: args.extractor = None
            if args.translator not in translators: args.translator = None
            if args.source not in lang_options.values(): args.source = None
            if args.target not in lang_options.values(): args.target = None
            if args.input and not os.path.exists(args.input): args.input = None

    # Iniciar workflow unificado
    try:
        success = run_workflow(args)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        cli.print_colored_line(f"\nErro fatal: {e}", 'red')
        import traceback
        traceback.print_exc()
        sys.exit(1)
