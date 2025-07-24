import os
import argostranslate.package
import argostranslate.translate
from argostranslatefiles import translate_file
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from qfluentwidgets import InfoBar

class TranslationWorker(QThread):
    finished_signal = pyqtSignal(str, bool)

    def __init__(self, input_path, from_code, to_code):
        super().__init__()
        self.input_path = input_path
        self.from_code = from_code
        self.to_code = to_code
        self._mutex = QMutex()
        self._abort = False

    def run(self):
        try:
            if not os.path.exists(self.input_path):
                self.finished_signal.emit("Input file not found", False)
                return


            # Initialize translation
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

            # Translate content
            self._mutex.lock()
            translate_file(translation, self.input_path)
            self._mutex.unlock()

            directory = os.path.dirname(self.input_path)
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            file_extension = os.path.splitext(self.input_path)[1].lower()
            default_name = os.path.join(directory, f"{base_name}_{self.to_code}{file_extension}")
            default_name = default_name.replace('\\', '/')

            if self._abort:
                return

            self.finished_signal.emit(default_name, True)

        except Exception as e:
            self.finished_signal.emit(f"Error during translation or saving: {str(e)}", False)
            print(str(e))

    def abort(self):
        self._mutex.lock()
        self._abort = True
        self._mutex.unlock()
        self.wait(500)


class FileTranslator:
    def __init__(self, parent_window, cfg):
        self.parent = parent_window
        self.cfg = cfg
        self.current_file_path = None

    def start_translation(self, file_path):
        if self.cfg.get(self.cfg.package).value == 'None':
            InfoBar.warning(
                title="Warning",
                content="No translation package selected. Please select one in Settings.",
                parent=self.parent
            )
            return

        self.current_file_path = file_path
        self.parent.progressbar.start()

        if hasattr(self, 'translation_worker'):
            self.translation_worker.abort()
            self.translation_worker.deleteLater()

        self.translate_file(file_path)

    def translate_file(self, file_path):
        """Start translation process"""
        lang_pair = self.cfg.get(self.cfg.package).value
        from_code, to_code = lang_pair.split('_')

        self.translation_worker = TranslationWorker(file_path, from_code, to_code)
        self.translation_worker.finished_signal.connect(self.parent.on_file_translation_done)
        self.translation_worker.start()
