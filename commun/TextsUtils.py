from commun.IntWrapper import IntWrapper


def dictToList(dictionary, extract=None):
    if extract is None:
        extract = []
    if isinstance(dictionary, (dict, list, tuple, set)):
        if isinstance(dictionary, dict):
            haystack = dictionary.items()
        elif isinstance(dictionary, (list, tuple)):
            haystack = enumerate(dictionary)
        else:  # set
            haystack = enumerate(list(dictionary))
        for key, value in haystack:
            dictToList(value, extract)
    elif isinstance(dictionary, str):
        extract.append(dictionary)
    return extract


def interactive_item(obj, texts, occurrences=None):
    if occurrences is None:
        occurrences = IntWrapper(0)
    if isinstance(obj, dict) or isinstance(obj, list):
        haystack = obj.items() if isinstance(obj, dict) else enumerate(obj)
        for key, value in haystack:
            if isinstance(value, str):
                current_index = occurrences.get()
                if current_index >= len(texts):
                    raise IndexError(
                        f"Não há textos suficientes. Índice {current_index} fora do range (tamanho: {len(texts)})"
                    )
                obj[key] = texts[current_index]
                occurrences.add(1)
            else:
                interactive_item(value, texts, occurrences)


def convert_special_chars_to_unicode(text):
    try:
        return text.encode('unicode_escape').decode('utf-8')
    except (AttributeError, UnicodeDecodeError, UnicodeEncodeError) as e:
        raise ValueError(f"Erro ao converter caracteres especiais para unicode: {e}")


def decode_unicode_escape(text):
    try:
        return text.encode('utf-8').decode('unicode_escape')
    except (AttributeError, UnicodeDecodeError, UnicodeEncodeError) as e:
        raise ValueError(f"Erro ao decodificar unicode escape: {e}")


import uuid
import re


def _generate_placeholder(prefix="__XTOK_"):
    """Gera um placeholder curto e (praticamente) único."""
    return f"{prefix}{uuid.uuid4().hex[:8]}__"


def mask_tokens_in_structure(obj, patterns, prefix="__XTOK_"):
    """
    Percorre uma estrutura (dict/list/tuple/str) e substitui trechos que casam com
    qualquer regex em `patterns` por placeholders únicos. Retorna (new_obj, mapping)

    - obj: estrutura que contém strings (pode ser dict/list/tuple/str)
    - patterns: lista de objetos compilados re.Pattern (a ordem importa)
    - prefix: prefixo do placeholder gerado

    mapping: dict {placeholder: original_text}
    """
    mapping = {}

    def mask_string(s):
        # Aplica cada padrão em ordem; cada match vira um placeholder
        for pat in patterns:
            # Substituição via função para guardar o original
            def _repl(m):
                orig = m.group(0)
                # não mascarar algo que já pareça um placeholder
                if isinstance(orig, str) and orig.startswith(prefix):
                    return orig
                ph = _generate_placeholder(prefix)
                # garantir unicidade
                while ph in mapping or ph in s:
                    ph = _generate_placeholder(prefix)
                mapping[ph] = orig
                return ph

            try:
                s = pat.sub(_repl, s)
            except Exception:
                # Em caso de algum problema com a regex, apenas pule
                continue
        return s

    def walk(o):
        if isinstance(o, str):
            return mask_string(o)
        elif isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        elif isinstance(o, list):
            return [walk(v) for v in o]
        elif isinstance(o, tuple):
            return tuple(walk(v) for v in o)
        else:
            return o

    return walk(obj), mapping


def unmask_tokens_in_structure(obj, mapping):
    """
    Restaura placeholders em `obj` usando o dicionário `mapping` (placeholder -> original).
    Funciona recursivamente sobre dict/list/tuple/str.
    """
    if not mapping:
        return obj

    # Ordenar por comprimento decrescente evita substituições parciais
    placeholders = sorted(mapping.keys(), key=len, reverse=True)
    try:
        pattern = re.compile("|".join(re.escape(p) for p in placeholders))
    except Exception:
        # fallback: nada a fazer
        pattern = None

    def unmask_string(s):
        if not pattern:
            return s

        def _repl(m):
            return mapping.get(m.group(0), m.group(0))

        try:
            return pattern.sub(_repl, s)
        except Exception:
            return s

    def walk(o):
        if isinstance(o, str):
            return unmask_string(o)
        elif isinstance(o, dict):
            return {k: walk(v) for k, v in o.items()}
        elif isinstance(o, list):
            return [walk(v) for v in o]
        elif isinstance(o, tuple):
            return tuple(walk(v) for v in o)
        else:
            return o

    return walk(obj)
