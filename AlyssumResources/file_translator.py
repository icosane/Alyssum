import os
import argostranslate.package
import argostranslate.translate
from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from docx.oxml import OxmlElement, CT_R, CT_P
from PyQt5.QtCore import QThread, pyqtSignal, QMutex
from qfluentwidgets import InfoBar

class TranslationWorker(QThread):
    request_save_path = pyqtSignal(str, str)
    finished_signal = pyqtSignal(str, bool)

    def __init__(self, input_path, from_code, to_code):
        super().__init__()
        self.input_path = input_path
        self.from_code = from_code
        self.to_code = to_code
        self._mutex = QMutex()
        self._abort = False
        self.save_path = ""
        self.translated_content = ""

    def run(self):
        try:
            if not os.path.exists(self.input_path):
                self.finished_signal.emit("Input file not found", False)
                return

            # Read and parse the file
            file_extension = os.path.splitext(self.input_path)[1].lower()
            if file_extension == '.txt':
                content = self._parse_txt(self.input_path)
            elif file_extension == '.docx':
                content = self._parse_docx(self.input_path)
            else:
                self.finished_signal.emit("Unsupported file format", False)
                return

            if not content:
                self.finished_signal.emit("No content found to translate", False)
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
            if file_extension == '.txt':
                translated_text = translation.translate(content)
            if file_extension == '.docx':
                translated_text = translation.translate(content)
            self._mutex.unlock()

            # Request save path
            base_name = os.path.splitext(os.path.basename(self.input_path))[0]
            default_name = f"{base_name}_translated_{self.to_code}{file_extension}"
            self.request_save_path.emit(default_name, translated_text)

            # Wait for save path or abort
            while not self._abort and not self.save_path:
                self.msleep(100)

            if self._abort:
                return

            if self.save_path:
                if file_extension == '.txt':
                    with open(self.save_path, 'w', encoding='utf-8') as f:
                        f.write(translated_text)
                elif file_extension == '.docx':
                    self._translate_docx(translated_text, self.save_path)

                self.finished_signal.emit(self.save_path, True)
            else:
                self.finished_signal.emit("", False)

        except Exception as e:
            self.finished_signal.emit(f"Error during translation or saving: {str(e)}", False)

    def _parse_txt(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading .txt file: {str(e)}")
            return ""

    def _parse_docx(self, path):
        try:
            doc = Document(path)
            self.original_doc = doc
            self.translatable_paragraphs = []

            texts_to_translate = []
            for para in doc.paragraphs:
                if self._has_translatable_text(para):
                    self.translatable_paragraphs.append(para)
                    texts_to_translate.append(para.text)
            return '\n'.join(texts_to_translate)
        except Exception as e:
            print(f"Error reading .docx file: {str(e)}")
            return ""

    def _has_translatable_text(self, para):
        # Allow paragraphs that have at least one text run
        return any(run.text.strip() for run in para.runs if not self._is_non_text_run(run))
    
    def _translate_docx(self, translated_text, save_path):
        if not hasattr(self, 'original_doc') or not hasattr(self, 'translatable_paragraphs'):
            return

        translated_lines = translated_text.split('\n')
        
        for para, trans_line in zip(self.translatable_paragraphs, translated_lines):
            if not para.runs or not trans_line:
                continue

            # Separate translatable and non-translatable runs
            translatable_runs = []
            non_translatable_runs = []
            for run in para.runs:
                if self._is_translatable_run(run):
                    translatable_runs.append(run)
                else:
                    non_translatable_runs.append(run)

            # If we have translatable runs, replace their text with translation
            if translatable_runs:
                # Clear all translatable runs first
                for run in translatable_runs:
                    run.text = ""
                
                # Put all translated text in the first translatable run
                translatable_runs[0].text = trans_line
                
                # Preserve non-translatable runs (hyperlinks, etc.)
                # They maintain their original position and content

        self.original_doc.save(save_path)

    def _is_translatable_run(self, run):
        """More accurate detection of translatable runs"""
        if not run.text.strip():
            return False
            
        xml = run._element.xml
        # Explicitly skip these elements
        skip_tags = {
            '<w:hyperlink',  # Hyperlinks
            '<w:instrText', # Field codes
            '<w:fldChar',    # Field characters
            '<w:drawing',    # Drawings
            '<w:pict',       # Pictures
            '<m:oMath',      # Math formulas
            '<w:footnote',   # Footnotes
            '<w:endnote',    # Endnotes
            '<m:sup',        # Superscript
            '<m:sub',        # subscript
            '<m:frac',       # a fraction
            '<m:msup',       # mathematical superscript
            '<a:blip',       # bitmap image
            '<a:shape',      # a shape
            '<a:groupShape', # a group of shapes
            '<a:line',       # a line shape
        }
        
        return not any(tag in xml for tag in skip_tags)



    def _is_non_text_run(self, run):
        """Returns True if the run contains drawing or hyperlink content"""
        xml = run._element.xml

        skip_tags = {
            '<w:hyperlink',  # Hyperlinks
            '<w:instrText', # Field codes
            '<w:fldChar',    # Field characters
            '<w:drawing',    # Drawings
            '<w:pict',       # Pictures
            '<m:oMath',      # Math formulas
            '<w:footnote',   # Footnotes
            '<w:endnote',    # Endnotes
            '<m:sup',        # Superscript
            '<m:sub',        # subscript
            '<m:frac',       # a fraction
            '<m:msup',       # mathematical superscript
            '<a:blip',       # bitmap image
            '<a:shape',      # a shape
            '<a:groupShape', # a group of shapes
            '<a:line',       # a line shape
        }

        #return ('<w:drawing' in xml or '<w:pict' in xml or '<w:hyperlink' in xml or '<w:instrText' in xml)
        return any(tag in xml for tag in skip_tags)



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
        self.translation_worker.request_save_path.connect(self.parent.handle_file_save_path)
        self.translation_worker.finished_signal.connect(self.parent.on_file_translation_done)
        self.translation_worker.start()
