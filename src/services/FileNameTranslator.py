import os
import shutil
from src import cli

class FileNameTranslator:
    def __init__(self, translate):
        self.translate = translate
        self.folderOutput = 'output'

        if not os.path.exists(self.folderOutput):
            os.makedirs(self.folderOutput)

    def process_directory(self, input_dir, keep_original=False):
        if not os.path.exists(input_dir):
            cli.print_colored_line(f"Erro: Pasta '{input_dir}' não encontrada.", 'red')
            return

        all_files_info = []
        for root, dirs, files in os.walk(input_dir):
            for f in files:
                rel_dir = os.path.relpath(root, input_dir)
                if rel_dir == ".":
                    rel_dir = ""
                
                name, ext = os.path.splitext(f)
                all_files_info.append({
                    'rel_dir': rel_dir,
                    'original_name': f,
                    'name_no_ext': name,
                    'ext': ext,
                    'full_src_path': os.path.join(root, f)
                })
        
        if not all_files_info:
            cli.print_colored_line("Nenhum arquivo encontrado na pasta ou subpastas.", 'yellow')
            return

        cli.print_colored_line(f"\nEncontrados {len(all_files_info)} arquivos em '{input_dir}' e suas subpastas.", 'cyan')

        # Extract names for translation
        file_names_to_translate = [info['name_no_ext'] for info in all_files_info]
            
        cli.print_colored_line(f"Traduzindo {len(file_names_to_translate)} nomes de arquivos...", 'cyan')
        
        # Translate names
        translated_names = self.translate.translate_batch(file_names_to_translate)
        
        if not translated_names or len(translated_names) != len(file_names_to_translate):
            cli.print_colored_line("Erro ao traduzir nomes de arquivos. Verifique a conexão ou as chaves de API.", 'red')
            return
            
        output_base = self.folderOutput
        processed_count = 0
        copied_originals = 0
        
        cli.print_colored_line(f"Salvando resultados em '{output_base}'...", 'cyan')

        for i, info in enumerate(all_files_info):
            src_path = info['full_src_path']
            
            # Recreate subdirectory structure in output
            target_dir = os.path.join(output_base, info['rel_dir'])
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)

            translated_file = f"{translated_names[i]}{info['ext']}"
            dst_path = os.path.join(target_dir, translated_file)
            
            # Copy with translated name
            try:
                # Use absolute paths for comparison to avoid skipping if they resolve to same file
                if os.path.abspath(src_path) != os.path.abspath(dst_path):
                    shutil.copy2(src_path, dst_path)
                    processed_count += 1
                
                # Keep original if requested
                if keep_original:
                    orig_dst_path = os.path.join(target_dir, info['original_name'])
                    if os.path.abspath(src_path) != os.path.abspath(orig_dst_path):
                        shutil.copy2(src_path, orig_dst_path)
                        copied_originals += 1
            except Exception as e:
                cli.print_colored_line(f"Erro ao processar arquivo '{info['original_name']}': {e}", 'red')
                    
        cli.print_colored_line(f"\n✓ Sucesso!", 'green')
        cli.print_colored_line(f"  - Arquivos traduzidos: {processed_count}", 'white')
        if keep_original:
            cli.print_colored_line(f"  - Originais mantidos: {copied_originals}", 'white')
        cli.print_colored_line(f"  - Localização: {os.path.abspath(output_base)}", 'white')
