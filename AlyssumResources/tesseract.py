import pytesseract
import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal
from qfluentwidgets import InfoBar

def thresholding(image):
    """Apply binary thresholding using Otsu's method"""
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

class OCRRWorker(QThread):
    finished_signal = pyqtSignal(str, bool)  # extracted_text, success

    def __init__(self, pixmap, lang):
        super().__init__()
        self.pixmap = pixmap
        self.lang = lang
        print(self.lang)

    def run(self):
        try:
            # Convert QPixmap to OpenCV image
            image = self.pixmap.toImage()
            height = image.height()
            width = image.width()
            buffer = image.bits()
            buffer.setsize(image.byteCount())
            cv_image = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 4)
            cv_image = cv2.cvtColor(cv_image, cv2.COLOR_RGBA2BGR)  # Convert to BGR

            # Preprocessing: Thresholding
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            thresh = thresholding(gray)

            # Perform OCR on preprocessed image
            extracted_text = pytesseract.image_to_string(thresh, lang=f'{self.lang}')
            self.finished_signal.emit(extracted_text, True)

        except Exception as e:
            self.finished_signal.emit(f"OCR Error: {str(e)}", False)


class OCR:
    def __init__(self, parent_window, cfg):
        self.parent = parent_window
        self.cfg = cfg
        self.set_package(self.cfg.package)

    def set_package(self, package):
        lang_pair = self.cfg.get(package).value
        if lang_pair != 'None':
            try:
                self.from_code, self.to_code = lang_pair.split('_')
                self.tesslang = self.get_shortened_language_code(self.from_code)
            except ValueError:
                pass


    def start_ocr_process(self, pixmap):
        """Entry point for OCR processing with preprocessing"""
        if not pixmap:
            InfoBar.warning(
                title="Warning",
                content="No screenshot captured.",
                duration=2000,
                parent=self.parent
            )
            return

        self.ocr_worker = OCRRWorker(pixmap, self.tesslang)
        self.ocr_worker.finished_signal.connect(self.parent.on_ocr_done)
        self.ocr_worker.start()

    def cancel_ocr(self):
        if hasattr(self, 'ocr_worker'):
            self.ocr_worker.abort()

    def get_shortened_language_code(self, language_code):
        language_mapping = {
            "ar": "ara",  # Arabic
            "az": "aze",  # Azerbaijani
            "bn": "ben",  # Bengali
            "bg": "bul",  # Bulgarian
            "ca": "cat",  # Catalan
            "cs": "ces",  # Czech
            "da": "dan",  # Danish
            "de": "deu",  # German
            "el": "ell",  # Greek
            "en": "eng",  # English
            "eo": "epo",  # Esperanto
            "et": "est",  # Estonian
            "fi": "fin",  # Finnish
            "fr": "fra",  # French
            "he": "heb",  # Hebrew
            "hi": "hin",  # Hindi
            "it": "ita",  # Italian
            "ja": "jpn",  # Japanese
            "ko": "kor",  # Korean
            "lv": "lav",  # Latvian
            "lt": "lit",  # Lithuanian
            "pl": "pol",  # Polish
            "pt": "por",  # Portuguese
            "ro": "ron",  # Romanian
            "ru": "rus",  # Russian
            "sk": "slk",  # Slovak
            "sl": "slv",  # Slovenian
            "es": "spa",  # Spanish
            "tr": "tur",  # Turkish
            "uk": "ukr"   # Ukrainian
        }

        return language_mapping.get(language_code, None)
