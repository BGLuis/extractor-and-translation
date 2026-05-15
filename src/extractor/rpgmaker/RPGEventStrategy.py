import re
from .RPGEventCodes import RPGEventCode
from .RPGTextFilters import RPGTextFilters

class EventStrategy:
    def extract(self, item, context=None):
        return None

    def insert(self, item, translated_text, context=None):
        pass

class ShowTextStrategy(EventStrategy):
    _text_keys = ["icon:", "secret:", "title:", "name:", "text:", "message:", "text1:", "text2:", "secretText:", "id:"]
    _title_pattern = re.compile(r'<([^<>]*)>|<<([^<>]*)>>')

    def extract(self, item, context=None):
        params = item.get('parameters', [])
        code = item.get('code')
        extracted = []
        for i, param in enumerate(params):
            if code == 101 and i == 0:
                continue
            if not RPGTextFilters.is_technical_or_code(param):
                title_match = self._title_pattern.search(param)
                if title_match:
                    groups = [group for group in title_match.groups() if group]
                    if groups:
                        title = groups[0]
                        text = param[title_match.end():].strip()
                        if text and not RPGTextFilters.is_technical_or_code(title):
                            extracted.append([title, text])
                elif any(param.startswith(key) for key in self._text_keys):
                    remaining_text = param.split(":", 1)[-1].strip()
                    if not RPGTextFilters.is_technical_or_code(remaining_text) and \
                       not RPGTextFilters.is_numeric(remaining_text) and \
                       not RPGTextFilters.is_boolean(remaining_text):
                        extracted.append(remaining_text)
                else:
                    extracted.append(param)
        
        if not extracted: return None
        return extracted[0] if len(extracted) == 1 else extracted

    def insert(self, item, text, context=None):
        if not text: return
        # Se 'text' for lista, pode ser [título, texto] ou vários parâmetros
        # Para simplificar, vamos ver se temos o mesmo número de parâmetros que extraímos
        
        params = item.get('parameters', [])
        code = item.get('code')
        if len(params) == 1:
            # Lógica legada para Show Text / Titles
            iten_text = params[0]
            new_text = text[1] if isinstance(text, list) and len(text) == 2 else text
            
            match = self._title_pattern.search(iten_text)
            if match:
                item['parameters'][0] = iten_text.replace(iten_text[match.end():].strip(), str(new_text).strip())
            elif any(iten_text.startswith(key) for key in self._text_keys):
                iten_text_parts = iten_text.split(":", 1)
                if len(iten_text_parts) > 1:
                    item['parameters'][0] = iten_text_parts[0] + ": " + str(new_text)
            else:
                item['parameters'][0] = str(new_text)
        else:
            # Para comandos multi-parâmetros (122, 101, etc.)
            # Precisamos encontrar QUAL parâmetro é texto.
            # Como a extração pegou o primeiro que não era técnico, vamos fazer o mesmo na inserção.
            for i in range(len(params)):
                if code == 101 and i == 0:
                    continue
                if not RPGTextFilters.is_technical_or_code(params[i]):
                    item['parameters'][i] = str(text)
                    break

class ChoiceStrategy(EventStrategy):
    _choice_condition_pattern = re.compile(r'^(?:if|show_if|hide_if|en|pt|ja|es|fr)\s*\(.*\)\s*', re.IGNORECASE)

    def extract(self, item, context=None):
        if not item.get('parameters'): return None
        choices = item['parameters'][0]
        if not choices: return None
        
        extracted = []
        for choice in choices:
            choice = choice.strip()
            match = self._choice_condition_pattern.match(choice)
            choice_text = choice[match.end():] if match else choice
            if not RPGTextFilters.is_technical_or_code(choice_text):
                extracted.append(choice_text)
        
        return extracted if extracted else None

    def insert(self, item, text, context=None):
        if not text or not isinstance(text, list): return
        original_list = item['parameters'][0]
        if len(original_list) != len(text): return
        
        final_list = []
        for orig, trans in zip(original_list, text):
            orig_clean = orig.strip()
            match = self._choice_condition_pattern.match(orig_clean)
            if match:
                prefix = match.group(0).rstrip()
                final_list.append(prefix + str(trans).strip())
            else:
                final_list.append(str(trans).strip())
        item['parameters'][0] = final_list

class ChoiceBranchStrategy(EventStrategy):
    def extract(self, item, context=None):
        params = item.get('parameters', [])
        if len(params) > 1:
            text = params[1]
            if not RPGTextFilters.is_technical_or_code(text):
                return text
        return None

    def insert(self, item, text, context=None):
        if not text: return
        params = item.get('parameters', [])
        if len(params) > 1:
            item['parameters'][1] = str(text)

class ScriptStrategy(EventStrategy):
    _quote_pattern = re.compile(r"'.*?'|\".*?\"")
    _subject_pattern = re.compile(r'\d_t=\d{2,}_subject=')
    
    # SAFELIST: Só extrair de funções conhecidas
    SAFE_FUNCTIONS = [
        re.compile(r"(?:\$gameMessage\.add|BattleManager\._logWindow\.push\('addText',|this\.addCommand|this\.setHelpWindowText)\s*\(\s*(['\"])(.*?)\1", re.IGNORECASE),
        re.compile(r"(?:mes|text)\s*=\s*(['\"])(.*?)\1", re.IGNORECASE)
    ]

    def extract(self, item, context=None):
        script_content = item['parameters'][0]
        if not isinstance(script_content, str): return None
        
        extracted = []
        for pattern in self.SAFE_FUNCTIONS:
            for match in pattern.finditer(script_content):
                text = match.group(2)
                if not RPGTextFilters.is_technical_or_code(text):
                    extracted.append(text)
        
        if not extracted and self._subject_pattern.search(script_content):
            extract_text = script_content.split('_subject=')[1].strip('"')
            if not RPGTextFilters.is_technical_or_code(extract_text):
                extracted.append(extract_text)

        if not extracted: return None
        return extracted[0] if len(extracted) == 1 else extracted

    def insert(self, item, text, context=None):
        if not text: return
        script_content = item['parameters'][0]
        text_to_insert = " ".join(text) if isinstance(text, list) else str(text)

        # Para inserção, o RPGMakerExtractor original usava uma lógica reversa com regex
        # Vamos manter uma lógica similar mas mais segura
        found = False
        for pattern in self.SAFE_FUNCTIONS:
            if pattern.search(script_content):
                # Substitui apenas o conteúdo do grupo 2 (o texto)
                def replacer(m):
                    return m.group(0).replace(m.group(2), text_to_insert)
                item['parameters'][0] = pattern.sub(replacer, script_content)
                found = True
                break
        
        if not found and self._subject_pattern.search(script_content):
            parts = script_content.split('_subject=')
            parts[1] = f'{text_to_insert}"'
            item['parameters'][0] = '_subject='.join(parts)

class PluginStrategyMZ(EventStrategy):
    TECHNICAL_KEYS = {
        'switchTypeEX', 'switchIdEX', 'targetIdEX', 'variableIdEX',
        'loop', 'smooth', 'volume', 'reload', 'autoplay', 'finishSwitch',
        'fileName', 'pitch', 'pan', 'wait', 'repeat', 'skippable',
        'WordWrap', 'FontFace', 'FontSize', 'TextSpeed', 'AutoColor',
        'MessageRows', 'MessageWidth', 'ChoiceLineHeight', 'ChoiceRows',
        'switchType', 'variableId', 'value', 'operation', 'operand',
        'image', 'picture', 'icon', 'se', 'bgm', 'bgs', 'me'
    }
    
    TEXT_KEYS = {'text', 'message', 'description', 'title', 'name', 'label', 'tooltip', 'help', 'content', 'body'}

    def extract(self, item, context=None):
        if len(item['parameters']) <= 3 or not isinstance(item['parameters'][3], dict):
            return None
        
        params = item['parameters'][3]
        extracted = {}
        for key, val in params.items():
            if key in self.TECHNICAL_KEYS: continue
            
            if isinstance(val, str) and not RPGTextFilters.is_technical_or_code(val):
                if key in self.TEXT_KEYS or len(val) > 3 or ' ' in val or any(c in val for c in '.,;:!?'):
                    extracted[key] = val
        
        if not extracted: return None
        if len(extracted) == 1 and 'text' in extracted: return extracted['text']
        return extracted

    def insert(self, item, text, context=None):
        if not text: return
        params = item['parameters'][3]
        if isinstance(text, dict):
            for key, val in text.items():
                if key in params:
                    params[key] = val
        elif isinstance(text, str) and 'text' in params:
            params['text'] = text

class PluginStrategyMV(EventStrategy):
    _prefixes = ["D_TEXT", "addLog", r"InformationWindow \d+ Text:", "mes ="]
    _compiled_prefixes = [re.compile(prefix) for prefix in _prefixes]

    def extract(self, item, context=None):
        content = item['parameters'][0]
        for compiled_prefix in self._compiled_prefixes:
            match = compiled_prefix.match(content)
            if match:
                prefix = match.group(0)
                split_result = content.split(prefix + " ", 1)
                if len(split_result) > 1:
                    text = split_result[1]
                    if not RPGTextFilters.is_technical_or_code(text):
                        return text
        return None

    def insert(self, item, text, context=None):
        if not text: return
        content = item['parameters'][0]
        for compiled_prefix in self._compiled_prefixes:
            match = compiled_prefix.match(content)
            if match:
                prefix = match.group(0)
                item['parameters'][0] = f'{prefix} {text}'
                break
