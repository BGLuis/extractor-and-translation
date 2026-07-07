import logging
from abc import ABC, abstractmethod
import src.utils.TextsUtils as TextsUtils

class TranslationContext:
    """Objeto de Contexto que viaja através do Pipeline"""
    def __init__(self, file_name, data, text, translate_instance, file_path_str, extractor):
        self.file_name = file_name
        self.data = data
        self.text = text  # Estado atual do texto
        self.original_text = text
        self.translate_instance = translate_instance
        self.file_path_str = file_path_str
        self.extractor = extractor
        self.mask_map = {}
        self.patterns = []


class PipelineStep(ABC):
    """Contrato base para um Middleware/Passo do Pipeline"""
    @abstractmethod
    def process(self, context: TranslationContext) -> TranslationContext:
        pass


class GetPatternsStep(PipelineStep):
    def process(self, context: TranslationContext) -> TranslationContext:
        context.patterns = context.extractor._get_patterns(context.file_name, context.data)
        return context


class MaskingStep(PipelineStep):
    def process(self, context: TranslationContext) -> TranslationContext:
        try:
            context.text, context.mask_map = TextsUtils.mask_tokens_in_structure(
                context.text, context.patterns, prefix="__XTOK_"
            )
        except Exception as e:
            logging.error(f"Erro no MaskingStep: {e}")
            context.mask_map = {}
        return context


class TranslationStep(PipelineStep):
    def process(self, context: TranslationContext) -> TranslationContext:
        def progress_callback(current, total):
            context.extractor.add_threads_status({
                'file': context.file_path_str,
                'status': 'process',
                'current': current,
                'total': total,
                'msg': f"Translating batch {current}/{total}"
            })

        context.extractor.add_threads_status({
            'file': context.file_path_str, 
            'status': 'process', 
            'msg': "Processing file via Pipeline"
        })
        
        context.text = context.translate_instance.translator(context.text, progress_callback)
        return context


class UnmaskingStep(PipelineStep):
    def process(self, context: TranslationContext) -> TranslationContext:
        try:
            if context.mask_map:
                context.text = TextsUtils.unmask_tokens_in_structure(context.text, context.mask_map)
        except Exception as e:
            logging.error(f"Erro no UnmaskingStep: {e}")
        return context


class FixingStep(PipelineStep):
    def process(self, context: TranslationContext) -> TranslationContext:
        try:
            context.extractor.fix_text_translate(context.text, context.original_text)
        except Exception as e:
            logging.error(f"Erro no FixingStep: {e}")
        return context


class TranslationPipeline:
    """Gerenciador do Pipeline (Chain of Responsibility modificado)"""
    def __init__(self):
        self.steps = []

    def add_step(self, step: PipelineStep):
        self.steps.append(step)
        return self

    def execute(self, context: TranslationContext) -> str:
        for step in self.steps:
            context = step.process(context)
        return context.text
