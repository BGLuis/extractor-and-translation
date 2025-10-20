from translate import *
from extractor import *

from extractor.BaseExtractor import BaseExtractor
from translate.BaseTranslate import BaseTranslate
import shutil
import cli
import os
import argparse
import sys

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


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Sistema de extração e tradução de textos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py --interactive
  python main.py -e RPGMaker -t Google -s pt -d en -i /path/to/input
  python main.py --extractor JsonExtractor --translator Ollama --source ja --target pt --input ./data --no-backup
  python main.py --list-extractors
  python main.py --list-translators
        """
    )

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
    extractors = list_subclasses_extractor()
    for name in extractors.keys():
        print(f"  - {name}")

    print("\n=== TRADUTORES DISPONÍVEIS ===")
    translators = list_subclasses_translate()
    for name in translators.keys():
        print(f"  - {name}")

    print("\n=== IDIOMAS SUPORTADOS ===")
    for lang_name, lang_code in lang_options.items():
        print(f"  - {lang_code}: {lang_name}")


def validate_arguments(args):
    errors = []

    if args.extractor:
        extractors = list_subclasses_extractor()
        if args.extractor not in extractors:
            errors.append(f"Extrator '{args.extractor}' não encontrado. Opções: {list(extractors.keys())}")

    if args.translator:
        translators = list_subclasses_translate()
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


def run_interactive_mode():
    extractor = cli.select_opition("Que Tipo de extrator de Texto vc gostaria:", list_subclasses_extractor())
    translator = cli.select_opition("Que Tipo de agente de tradução vc gostaria:", list_subclasses_translate())
    translate = translator()

    lang_source = cli.select_opition("Selecione o idioma de origem:", lang_options)
    remove_lang_options(lang_source)
    lang_target = cli.select_opition("Selecione o idioma de destino:", lang_options)

    translate.change_language(lang_source, lang_target)

    translator_questions = translator.get_interactive_questions()
    if translator_questions:
        cli.clear_screen()
        translator_config = {}

        for question in translator_questions:
            if 'title' in question:
                cli.print_colored_line(question['title'], 'cyan')

            if 'description' in question:
                color = question.get('color', 'yellow')
                cli.print_colored_line(question['description'], color)

            cli.print_colored_line(question['question'], question.get('color', 'white'))

            answer = input().strip()
            if answer or not question.get('required', False):
                translator_config[question['key']] = answer
                if answer:
                    cli.print_colored_line(f"\n✓ {question['key'].capitalize()} configurado com sucesso!", 'green')
                else:
                    cli.print_colored_line(f"\n⚠ Continuando sem {question['key']}.", 'yellow')
            else:
                cli.print_colored_line(f"\n✗ {question['key'].capitalize()} é obrigatório!", 'red')
                return False

        translate.apply_configuration(translator_config)

    cli.clear_screen()
    extractor = extractor(translate)

    extractor_questions = extractor.get_interactive_questions()
    if extractor_questions:
        cli.clear_screen()
        extractor_config = {}

        for question in extractor_questions:
            if 'title' in question:
                cli.print_colored_line(question['title'], 'cyan')

            if 'description' in question:
                color = question.get('color', 'yellow')
                cli.print_colored_line(question['description'], color)

            cli.print_colored_line(question['question'], question.get('color', 'white'))

            answer = input().strip()
            if answer or not question.get('required', False):
                extractor_config[question['key']] = answer
                if answer:
                    cli.print_colored_line(f"\n✓ {question['key'].capitalize()} configurado com sucesso!", 'green')
                else:
                    cli.print_colored_line(f"\n⚠ Continuando sem {question['key']}.", 'yellow')
            else:
                cli.print_colored_line(f"\n✗ {question['key'].capitalize()} é obrigatório!", 'red')
                return False

        extractor.apply_configuration(extractor_config)

    extractor.init_folder()

    cli.instruction(f"Precione enter para selecionar a pasta de entrada dos arquivos")
    dir = cli.select_folder("Selecione a pasta de entrada dos arquivos")
    if dir is None:
        cli.print_colored_line("Nenhuma pasta selecionada. Encerrando o programa.", 'red')
        return False

    return run_extraction_process(extractor, translate, dir, lang_source, backup=True, verify=True)


def run_command_line_mode(args):
    extractors = list_subclasses_extractor()
    translators = list_subclasses_translate()

    extractor_class = extractors[args.extractor]
    translator_class = translators[args.translator]

    translate = translator_class()
    translate.change_language(args.source, args.target)

    if args.synopsis:
        config = {'synopsis': args.synopsis}
        translate.apply_configuration(config)
        cli.print_colored_line(f"✓ Sinopse configurada", 'green')

    extractor = extractor_class(translate)
    extractor.init_folder()

    cli.print_colored_line(f"Usando extrator: {args.extractor}", 'cyan')
    cli.print_colored_line(f"Usando tradutor: {args.translator}", 'cyan')
    cli.print_colored_line(f"Traduzindo de {args.source} para {args.target}", 'cyan')
    cli.print_colored_line(f"Pasta de entrada: {args.input}", 'cyan')

    return run_extraction_process(
        extractor, translate, args.input, args.source,
        backup=not args.no_backup,
        verify=not args.no_verify
    )


def run_extraction_process(extractor, translate, input_dir, lang_source, backup=True, verify=True):
    """Run the main extraction and translation process"""
    try:
        if backup:
            backup_dir = input_dir + "-" + lang_source
            cli.print_colored_line(f"Criando backup em: {backup_dir}", 'yellow')
            copy_files_only(input_dir, backup_dir)

        copy_files_only(input_dir, extractor.folderInput)

        cli.print_colored_line("Iniciando processamento dos arquivos...", 'green')
        extractor.process_files()
        cli.show_status(extractor.threads_status)

        if verify:
            cli.instruction(f"Verifique a tradução dos arquivos na pasta '{extractor.folderProcess}', e pressione enter tecla para continuar")

        cli.print_colored_line("Exportando arquivos", 'green')
        extractor.import_files()
        copy_files_only(extractor.folderOutput, input_dir)

        translate.save_cache()
        cli.print_colored_line("Tradução finalizada com sucesso!", 'green')

        return True

    except Exception as e:
        cli.print_colored_line(f"Erro durante o processamento: {str(e)}", 'red')
        return False


if __name__ == '__main__':
    args = parse_arguments()

    if args.list_extractors or args.list_translators or args.list_languages:
        if args.list_extractors:
            print("\n=== EXTRATORES DISPONÍVEIS ===")
            extractors = list_subclasses_extractor()
            for name in extractors.keys():
                print(f"  - {name}")

        if args.list_translators:
            print("\n=== TRADUTORES DISPONÍVEIS ===")
            translators = list_subclasses_translate()
            for name in translators.keys():
                print(f"  - {name}")

        if args.list_languages:
            print("\n=== IDIOMAS SUPORTADOS ===")
            for lang_name, lang_code in lang_options.items():
                print(f"  - {lang_code}: {lang_name}")

        sys.exit(0)

    if args.interactive or not any([args.extractor, args.translator, args.source, args.target, args.input]):
        success = run_interactive_mode()
        sys.exit(0 if success else 1)

    errors = validate_arguments(args)
    if errors:
        cli.print_colored_line("Erros encontrados:", 'red')
        for error in errors:
            cli.print_colored_line(f"  - {error}", 'red')
        cli.print_colored_line("\nUse --help para ver a ajuda completa", 'yellow')
        sys.exit(1)

    if not all([args.extractor, args.translator, args.source, args.target, args.input]):
        missing = []
        if not args.extractor: missing.append("--extractor")
        if not args.translator: missing.append("--translator")
        if not args.source: missing.append("--source")
        if not args.target: missing.append("--target")
        if not args.input: missing.append("--input")

        cli.print_colored_line(f"Argumentos obrigatórios ausentes: {', '.join(missing)}", 'red')
        cli.print_colored_line("Use --interactive para modo interativo ou forneça todos os argumentos", 'yellow')
        sys.exit(1)

    success = run_command_line_mode(args)
    sys.exit(0 if success else 1)
