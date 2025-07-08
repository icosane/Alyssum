import argostranslate.package
import argostranslate.translate
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from qfluentwidgets import InfoBar

class TranslationWorker(QThread):
    finished_signal = pyqtSignal(str, bool)  # translated_text, success
    progress_updated = pyqtSignal(int)

    def __init__(self, input_text, from_code, to_code):
        super().__init__()
        self.input_text = input_text
        self.from_code = from_code
        self.to_code = to_code
        self._mutex = QMutex()
        self._abort = False

    def run(self):
        try:
            # Check if languages are installed
            installed_languages = argostranslate.translate.get_installed_languages()
            from_lang = next((lang for lang in installed_languages if lang.code == self.from_code), None)
            to_lang = next((lang for lang in installed_languages if lang.code == self.to_code), None)

            if not from_lang or not to_lang:
                self.finished_signal.emit("Required language package not installed", False)
                return

            translation = from_lang.get_translation(to_lang)
            if not translation:
                self.finished_signal.emit("Translation between these languages not available", False)
                return

            # Translate
            self.progress_updated.emit(0)
            if self._abort:
                self.finished_signal.emit("Translation cancelled", False)
                return

            translated_text = translation.translate(self.input_text)
            self.progress_updated.emit(100)

            if self._abort:
                self.finished_signal.emit("Translation cancelled", False)
            else:
                self.finished_signal.emit(translated_text, True)

        except Exception as e:
            self.finished_signal.emit(f"Translation error: {str(e)}", False)

    def abort(self):
        self._mutex.lock()
        self._abort = True
        self._mutex.unlock()
        self.wait()


class TextTranslator:
    def __init__(self, parent_window, cfg):
        self.parent = parent_window
        self.cfg = cfg

    def start_translation(self, input_text):
        """Entry point for translating input text"""
        if self.cfg.get(self.cfg.package).value == 'None':
            InfoBar.warning(
                title="Warning",
                content="No translation package selected. Please select one in Settings.",
                duration=2000,
                parent=self.parent
            )
            return

        lang_pair = self.cfg.get(self.cfg.package).value
        from_code, to_code = lang_pair.split('_')

        self.translation_worker = TranslationWorker(input_text, from_code, to_code)
        self.translation_worker.finished_signal.connect(self.parent.on_translation_done)
        #self.translation_worker.progress_updated.connect(self.parent.update_translation_progress)
        self.translation_worker.start()

    def cancel_translation(self):
        if hasattr(self, 'translation_worker'):
            self.translation_worker.abort()
