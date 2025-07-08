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

    def __init__(self, pixmap):
        super().__init__()
        self.pixmap = pixmap

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
            extracted_text = pytesseract.image_to_string(thresh)
            self.finished_signal.emit(extracted_text, True)

        except Exception as e:
            self.finished_signal.emit(f"OCR Error: {str(e)}", False)


class OCR:
    def __init__(self, parent_window, cfg):
        self.parent = parent_window
        self.cfg = cfg

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

        self.ocr_worker = OCRRWorker(pixmap)
        self.ocr_worker.finished_signal.connect(self.parent.on_ocr_done)
        self.ocr_worker.start()

    def cancel_ocr(self):
        if hasattr(self, 'ocr_worker'):
            self.ocr_worker.abort()
