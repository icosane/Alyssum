import sys, os
from PyQt5.QtGui import QColor, QIcon, QFont, QPixmap, QPainter, QPen, QImage
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QStackedWidget
from PyQt5.QtCore import Qt, pyqtSignal, QTranslator, QCoreApplication, pyqtSlot, QRect, QTimer, QObject
sys.stdout = open(os.devnull, 'w')
import warnings
warnings.filterwarnings("ignore")
from qfluentwidgets import setThemeColor, TransparentToolButton, FluentIcon, PushSettingCard, isDarkTheme, MessageBox, FluentTranslator, IndeterminateProgressBar, PushButton, SubtitleLabel, ComboBoxSettingCard, OptionsSettingCard, HyperlinkCard, ScrollArea, InfoBar, InfoBarPosition, StrongBodyLabel, TransparentTogglePushButton, TextBrowser, TextEdit,  SwitchSettingCard
from winrt.windows.ui.viewmanagement import UISettings, UIColorType
from AlyssumResources.config import cfg, TranslationPackage
from AlyssumResources.argos_utils import update_package
from AlyssumResources.translator import TextTranslator
from AlyssumResources.tesseract import OCR
import shutil
import traceback
import glob
from pathlib import Path
import pyautogui, re


if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    base_dir = os.path.dirname(sys.executable)  # Points to build/
    res_dir = os.path.join(sys.prefix)
else:
    # Running as a script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = base_dir

class ErrorHandler(object):
    def __call__(self, exctype, value, tb):
        # Extract the traceback details
        tb_info = traceback.extract_tb(tb)
        # Get the last entry in the traceback (the most recent call)
        last_call = tb_info[-1] if tb_info else None

        if last_call:
            filename, line_number, function_name, text = last_call
            error_message = (f"Type: {exctype.__name__}\n"
                             f"Message: {value}\n"
                             f"File: {filename}\n"
                             f"Line: {line_number}\n"
                             f"Code: {text}")
        else:
            error_message = (f"Type: {exctype.__name__}\n"
                             f"Message: {value}")

        error_box = MessageBox("Error", error_message, parent=window)
        error_box.cancelButton.hide()
        error_box.buttonLayout.insertStretch(1)
        error_box.exec()

    def write(self, message):
        if message.startswith("Error:"):
            error_box = MessageBox("Error", message, parent=window)
            error_box.cancelButton.hide()
            error_box.buttonLayout.insertStretch(1)
            error_box.exec()
        else:
            pass

    def flush(self):
        pass

class ScreenshotOverlay(QWidget):
    screenshot_taken = pyqtSignal(QPixmap)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        self.setGeometry(screen_geometry)

        self.start_point = None
        self.end_point = None
        self.is_drawing = False
        self.selection_rect = None

    def paintEvent(self, event):
        painter = QPainter(self)

        # Semi-transparent dark overlay
        if not self.selection_rect:
            # Semi-transparent dark overlay
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))

        # If a selection is being made
        if self.selection_rect:
            # Set up a transparent brush and red pen
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)  # Make the fill transparent

            # Draw the selection rectangle
            painter.drawRect(self.selection_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_drawing = True
            self.selection_rect = None
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_point = event.pos()
            self.selection_rect = QRect(
                min(self.start_point.x(), self.end_point.x()),
                min(self.start_point.y(), self.end_point.y()),
                abs(self.end_point.x() - self.start_point.x()),
                abs(self.end_point.y() - self.start_point.y())
            )
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.end_point = event.pos()
            self.is_drawing = False

            #screen = QApplication.primaryScreen()
            #screen_geometry = screen.geometry()

            # Correctly calculate coordinates
            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())

            width = x2 - x1
            height = y2 - y1

            # **DEBUG** Print coordinates
            '''print("Capture Region:")
            print(f"x1: {x1}, y1: {y1}")
            print(f"x2: {x2}, y2: {y2}")
            print(f"Width: {width}, Height: {height}")'''

            # Only capture if selection is larger than a few pixels
            if width > 5 and height > 5:
                # Capture the actual screen region
                screenshot = pyautogui.screenshot(region=(x1, y1, width, height))

                # **ADJUSTED CONVERSION**
                screenshot = screenshot.convert('RGB')  # Ensure RGB mode
                qimage = QImage(
                    screenshot.tobytes('raw', 'RGB'),
                    screenshot.width,
                    screenshot.height,
                    screenshot.width * 3,  # Explicit stride assumption
                    QImage.Format_RGB888
                )
                pixmap = QPixmap.fromImage(qimage)

                # Close overlay before emitting screenshot
                self.close()

                # Slight delay to ensure overlay is closed
                QTimer.singleShot(100, lambda: self.screenshot_taken.emit(pixmap))
            else:
                # If selection is too small, just close the overlay
                self.close()



    def keyPressEvent(self, event):
        # Allow closing the overlay with Escape key
        if event.key() == Qt.Key_Escape:
            self.close()

class ScreenshotTool(QObject):
    screenshot_taken = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.overlay = None

    def capture_screenshot(self):
        # Slight delay to allow releasing of keys
        QApplication.processEvents()
        QTimer.singleShot(200, self._show_overlay)

    def _show_overlay(self):
        self.overlay = ScreenshotOverlay()
        self.overlay.screenshot_taken.connect(self.handle_screenshot)
        self.overlay.show()

    def handle_screenshot(self, pixmap):
        # 1. Save to file
        '''file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.parent,
            "Save Screenshot",
            "",
            "Image Files (*.png *.jpg *.bmp)"
        )
        if file_path:
            pixmap.save(file_path)'''

        # 2. Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(pixmap)

        # 3. Emit to other window
        self.screenshot_taken.emit(pixmap)

        # Optional: You can add more actions here
        # For example, send to another method in your main application


class PlainTextEdit(TextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptRichText(False)  # Prevent rich text input
        self.textChanged.connect(self._on_text_changed)

    def paste(self):
        clipboard = QApplication.clipboard()
        if clipboard.mimeData().hasText():
            self.insertPlainText(clipboard.text())
        else:
            super().paste()

    def insertFromMimeData(self, source):
        # This handles paste, drag-and-drop, and context-menu paste
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            pass  # Optionally handle other formats

    def _on_text_changed(self):
        # Ensure any HTML-like content is removed
        cursor = self.textCursor()
        pos = cursor.position()

        html = self.toHtml()
        plain_text = self.toPlainText()

        if html != plain_text:
            self.blockSignals(True)
            self.setPlainText(plain_text)
            self.blockSignals(False)

            # Restore cursor position
            cursor.setPosition(pos)
            self.setTextCursor(cursor)

class MainWindow(QMainWindow):
    theme_changed = pyqtSignal()
    package_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "Alyssum"))
        self.setWindowIcon(QIcon(os.path.join(res_dir, "AlyssumResources", "assets", "icon.ico")))
        self.setGeometry(100,100,700,850)
        self.setMinimumSize(700,850)
        self.last_directory = ""
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.lang_buttons = {
            'main': {},
            'settings': {}
        }

        self.lang_layout_main = QHBoxLayout()
        self.lang_widget_main = QWidget()
        self.lang_widget_main.setLayout(self.lang_layout_main)
        self.lang_layout_main.addStretch()
        self.lang_layout_settings = QHBoxLayout()
        self.lang_widget_settings = QWidget()
        self.lang_widget_settings.setLayout(self.lang_layout_settings)
        self.lang_layout_settings.addStretch()

        self.main_layout()
        self.settings_layout()
        self.setup_theme()
        self.center()

        self.theme_changed.connect(self.update_theme)
        self.package_changed.connect(lambda: update_package(self))

        self.translator = TextTranslator(self, cfg)
        self.screenshot_tool = ScreenshotTool(parent=self)
        self.screenshot_tool.screenshot_taken.connect(self.on_screenshot_taken)
        self.ocr = OCR(self, cfg)

    def setup_theme(self):
        main_color_hex = self.get_main_color_hex()
        setThemeColor(main_color_hex)
        if isDarkTheme():
            theme_stylesheet = """
                QWidget {
                    background-color: #1e1e1e;  /* Dark background */
                    border: none;
                }
                QFrame {
                    background-color: transparent;
                    border: none;
                }
            """
        else:
            theme_stylesheet = """
                QWidget {
                    background-color: #f0f0f0;  /* Light background */
                    border: none;
                }
                QFrame {
                    background-color: transparent;
                    border: none;
                }
            """
        QApplication.instance().setStyleSheet(theme_stylesheet)

    def get_main_color_hex(self):
        color = UISettings().get_color_value(UIColorType.ACCENT)
        return f'#{int((color.r)):02x}{int((color.g)):02x}{int((color.b )):02x}'

    def update_theme(self):
        self.setup_theme()

    def center(self):
        screen_geometry = self.screen().availableGeometry()
        window_geometry = self.geometry()

        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2

        self.move(x, y)

    def update_argos_remove_button_state(self,enabled):
        if hasattr(self, 'card_deleteargosmodel'):
            self.card_deleteargosmodel.button.setEnabled(enabled)

    def screenshot_start(self):
        window.showMinimized()
        self.screenshot_tool.capture_screenshot()

    def on_screenshot_taken(self, pixmap: QPixmap):
        if pixmap:
            self.start_ocr_process(pixmap)
        else:
            # Handle the case where pixmap is empty (if ever occurs)
            InfoBar.warning(
                title="Warning",
                content="No valid screenshot captured.",
                duration=2000,
                parent=self
            )

    def clean_text(self, text):
        paragraphs = text.split('\n\n')

        cleaned_paragraphs = []
        for paragraph in paragraphs:
            cleaned_paragraph = paragraph.replace('\n', ' ')

            cleaned_paragraph = re.sub(r'\s+', ' ', cleaned_paragraph).strip()

            cleaned_paragraphs.append(cleaned_paragraph)

        text = '\n\n'.join(cleaned_paragraphs)
        return text

    def main_layout(self):
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        main_layout.addWidget(self.lang_widget_main)
        self.check_packages()

        font = QFont()
        font.setPointSize(14)
        self.textinputw = PlainTextEdit()
        self.textinputw.setFont(font)
        main_layout.addWidget(self.textinputw)

        self.tl_button = PushButton(QCoreApplication.translate("MainWindow",'Translate'))
        button_layout.addWidget(self.tl_button)
        self.cl_button = PushButton(QCoreApplication.translate("MainWindow",'Clear'))
        button_layout.addWidget(self.cl_button)
        main_layout.addLayout(button_layout)
        main_layout.setAlignment(button_layout, Qt.AlignCenter)

        self.textoutputw = TextBrowser()
        self.textoutputw.setFont(font)
        main_layout.addWidget(self.textoutputw)

        self.settings_button = TransparentToolButton(FluentIcon.SETTING)
        self.copy_button = TransparentToolButton(FluentIcon.COPY)
        self.ocr_button = TransparentToolButton(FluentIcon.CAMERA)

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.settings_button)
        settings_layout.addWidget(self.copy_button)
        settings_layout.addWidget(self.ocr_button)
        settings_layout.addStretch()
        settings_layout.setContentsMargins(5, 5, 5, 5)

        main_layout.addLayout(settings_layout)

        #connect
        self.settings_button.clicked.connect(self.show_settings_page)
        self.copy_button.clicked.connect(self.selectandcopy)
        self.ocr_button.clicked.connect(self.screenshot_start)
        self.tl_button.clicked.connect(self.start_translation_process)
        self.cl_button.clicked.connect(self.clearinpoutw)

        main_widget = QWidget()
        main_widget.setLayout(main_layout)
        self.stacked_widget.addWidget(main_widget)

    def settings_layout(self):
        settings_layout = QVBoxLayout()

        back_button_layout = QHBoxLayout()

        back_button = TransparentToolButton(FluentIcon.LEFT_ARROW)
        back_button.clicked.connect(self.show_main_page)

        back_button_layout.addWidget(back_button, alignment=Qt.AlignmentFlag.AlignTop)
        back_button_layout.setContentsMargins(5, 5, 5, 5)

        settings_layout.addLayout(back_button_layout)

        self.settings_title = SubtitleLabel(QCoreApplication.translate("MainWindow", "Settings"))
        self.settings_title.setTextColor(QColor(0, 0, 0), QColor(255, 255, 255))

        back_button_layout.addWidget(self.settings_title, alignment=Qt.AlignmentFlag.AlignTop)

        card_layout = QVBoxLayout()

        self.modelsins_title = StrongBodyLabel(QCoreApplication.translate("MainWindow", "Model management"))
        self.modelsins_title.setTextColor(QColor(0, 0, 0), QColor(255, 255, 255))
        card_layout.addSpacing(20)
        card_layout.addWidget(self.modelsins_title, alignment=Qt.AlignmentFlag.AlignTop)

        self.card_settlpackage = ComboBoxSettingCard(
            configItem=cfg.package,
            icon=FluentIcon.CLOUD_DOWNLOAD,
            title=QCoreApplication.translate("MainWindow","Argos Translate package"),
            content=QCoreApplication.translate("MainWindow", "Change translation package"),
            texts=[
                "None", "sq_en", "ar_en", "az_en", "eu_en", "bn_en", "bg_en", "ca_en", "zh_tw_en", "zh_en",
                "cs_en", "da_en", "nl_en", "en_sq", "en_ar", "en_az", "en_eu", "en_bn", "en_bg",
                "en_ca", "en_zh", "en_zh_tw", "en_cs", "en_da", "en_nl", "en_eo", "en_et", "en_fi",
                "en_fr", "en_gl", "en_de", "en_el", "en_he", "en_hi", "en_hu", "en_id", "en_ga",
                "en_it", "en_ja", "en_ko", "en_ky", "en_lv", "en_lt", "en_ms", "en_no", "en_fa", "en_pl",
                "en_pt", "en_pt_br", "en_ro", "en_ru", "en_sk", "en_sl", "en_es", "en_sv", "en_tl",
                "en_th", "en_tr", "en_uk", "en_ur", "eo_en", "et_en", "fi_en", "fr_en", "gl_en",
                "de_en", "el_en", "he_en", "hi_en", "hu_en", "id_en", "ga_en", "it_en", "ja_en",
                "ko_en", "ky_en", "lv_en", "lt_en", "ms_en", "no_en", "fa_en", "pl_en", "pt_br_en", "pt_en",
                "pt_es", "ro_en", "ru_en", "sk_en", "sl_en", "es_en", "es_pt", "sv_en", "tl_en",
                "th_en", "tr_en", "uk_en", "ur_en"
            ]


        )

        card_layout.addWidget(self.card_settlpackage, alignment=Qt.AlignmentFlag.AlignTop)
        cfg.package.valueChanged.connect(self.package_changed.emit)

        card_layout.addWidget(self.lang_widget_settings)
        self.check_packages()

        self.card_deleteargosmodel = PushSettingCard(
            text=QCoreApplication.translate("MainWindow","Remove"),
            icon=FluentIcon.BROOM,
            title=QCoreApplication.translate("MainWindow","Remove Argos Translate package"),
            content=QCoreApplication.translate("MainWindow", "Delete currently selected translation package. Will be removed: <b>{}</b>").format(cfg.get(cfg.package).value),
        )

        card_layout.addWidget(self.card_deleteargosmodel, alignment=Qt.AlignmentFlag.AlignTop)
        self.card_deleteargosmodel.clicked.connect(self.packageremover)
        if ((cfg.get(cfg.package).value == 'None')):
            self.card_deleteargosmodel.button.setDisabled(True)

        self.miscellaneous_title = StrongBodyLabel(QCoreApplication.translate("MainWindow", "Miscellaneous"))
        self.miscellaneous_title.setTextColor(QColor(0, 0, 0), QColor(255, 255, 255))
        card_layout.addSpacing(20)
        card_layout.addWidget(self.miscellaneous_title, alignment=Qt.AlignmentFlag.AlignTop)

        self.card_shortcuts = SwitchSettingCard(
            icon=FluentIcon.TILES,
            title=QCoreApplication.translate("MainWindow","Enable keyboard shortcuts"),
            content=QCoreApplication.translate("MainWindow","Press F1 to translate, F2 to clear windows, F3 to copy translation to the clipboard."),
            configItem=cfg.shortcuts
        )
        card_layout.addWidget(self.card_shortcuts, alignment=Qt.AlignmentFlag.AlignTop)

        self.card_setlanguage = ComboBoxSettingCard(
            configItem=cfg.language,
            icon=FluentIcon.LANGUAGE,
            title=QCoreApplication.translate("MainWindow","Language"),
            content=QCoreApplication.translate("MainWindow", "Change UI language"),
            texts=["English", "Русский"]
        )

        card_layout.addWidget(self.card_setlanguage, alignment=Qt.AlignmentFlag.AlignTop)
        cfg.language.valueChanged.connect(self.restartinfo)

        self.card_theme = OptionsSettingCard(
            cfg.themeMode,
            FluentIcon.BRUSH,
            QCoreApplication.translate("MainWindow","Application theme"),
            QCoreApplication.translate("MainWindow", "Adjust how the application looks"),
            [QCoreApplication.translate("MainWindow","Light"), QCoreApplication.translate("MainWindow","Dark"), QCoreApplication.translate("MainWindow","Follow System Settings")]
        )

        card_layout.addWidget(self.card_theme, alignment=Qt.AlignmentFlag.AlignTop)
        self.card_theme.optionChanged.connect(self.theme_changed.emit)

        self.card_zoom = OptionsSettingCard(
            cfg.dpiScale,
            FluentIcon.ZOOM,
            QCoreApplication.translate("MainWindow","Interface zoom"),
            QCoreApplication.translate("MainWindow","Change the size of widgets and fonts"),
            texts=[
                "100%", "125%", "150%", "175%", "200%",
                QCoreApplication.translate("MainWindow","Follow System Settings")
            ]
        )

        card_layout.addWidget(self.card_zoom, alignment=Qt.AlignmentFlag.AlignTop)
        cfg.dpiScale.valueChanged.connect(self.restartinfo)

        self.card_ab = HyperlinkCard(
            url="https://github.com/icosane/Alyssum",
            text="Github",
            icon=FluentIcon.INFO,
            title=QCoreApplication.translate("MainWindow", "About"),
            content=QCoreApplication.translate("MainWindow", "Simple local translator based on ArgosTranslate")
        )
        card_layout.addWidget(self.card_ab,  alignment=Qt.AlignmentFlag.AlignTop )

        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.card_widget = QWidget()
        self.card_widget.setLayout(card_layout)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.card_widget)
        settings_layout.addWidget(self.scroll_area)

        self.download_progressbar = IndeterminateProgressBar(start=False)
        settings_layout.addWidget(self.download_progressbar )

        settings_widget = QWidget()
        settings_widget.setLayout(settings_layout)

        self.stacked_widget.addWidget(settings_widget)

    def show_settings_page(self):
        self.stacked_widget.setCurrentIndex(1)  # Switch to the settings page

    def show_main_page(self):
        self.stacked_widget.setCurrentIndex(0)  # Switch back to the main page

    def clearinpoutw(self):
        self.textoutputw.clear()
        self.textinputw.clear()

    def selectandcopy(self):
        self.textoutputw.selectAll()
        self.textoutputw.copy()

        InfoBar.success(
            title=QCoreApplication.translate("MainWindow", "Success"),
            content=QCoreApplication.translate("MainWindow", "Successfully copied to the clipboard"),
            orient=Qt.Orientation.Horizontal,
            isClosable=False,
            position=InfoBarPosition.BOTTOM,
            duration=4000,
            parent=self
        )

    def keyPressEvent(self, event):
        if (cfg.get(cfg.shortcuts) is True):
            if event.key() == Qt.Key_F1:
                self.tl_button.click()
            elif event.key() == Qt.Key_F2:
                self.cl_button.click()
            elif event.key() == Qt.Key_F3:
                self.selectandcopy()
        super().keyPressEvent(event)

    def check_packages(self):

        languages = {
            'en_ru': 'English → Russian',
            'ru_en': 'Russian → English',
            'de_en': 'German → English',
            'fr_en': 'French → English',
            'it_en': 'Italian → English',
            'ja_en': 'Japanese → English',
            'sq_en': 'Albanian → English',
            'ar_en': 'Arabic → English',
            'az_en': 'Azerbaijani → English',
            'eu_en': 'Basque → English',
            'bn_en': 'Bengali → English',
            'bg_en': 'Bulgarian → English',
            'ca_en': 'Catalan → English',
            'zt_en': 'Chinese (traditional) → English',
            'zh_en': 'Chinese → English',
            'cs_en': 'Czech → English',
            'da_en': 'Danish → English',
            'nl_en': 'Dutch → English',
            'en_sq': 'English → Albanian',
            'en_ar': 'English → Arabic',
            'en_az': 'English → Azerbaijani',
            'en_eu': 'English → Basque',
            'en_bn': 'English → Bengali',
            'en_bg': 'English → Bulgarian',
            'en_ca': 'English → Catalan',
            'en_zh': 'English → Chinese',
            'en_zt': 'English → Chinese (traditional)',
            'en_cs': 'English → Czech',
            'en_da': 'English → Danish',
            'en_nl': 'English → Dutch',
            'en_eo': 'English → Esperanto',
            'en_et': 'English → Estonian',
            'en_fi': 'English → Finnish',
            'en_fr': 'English → French',
            'en_gl': 'English → Galician',
            'en_de': 'English → German',
            'en_el': 'English → Greek',
            'en_he': 'English → Hebrew',
            'en_hi': 'English → Hindi',
            'en_hu': 'English → Hungarian',
            'en_id': 'English → Indonesian',
            'en_ga': 'English → Irish',
            'en_it': 'English → Italian',
            'en_ja': 'English → Japanese',
            'en_ko': 'English → Korean',
            'en_ky': 'English → Kyrgyz',
            'en_lv': 'English → Latvian',
            'en_lt': 'English → Lithuanian',
            'en_ms': 'English → Malay',
            'en_nb': 'English → Norwegian Bokmal',
            'en_fa': 'English → Persian',
            'en_pl': 'English → Polish',
            'en_pt': 'English → Portuguese',
            'en_pb': 'English → Portuguese (Brazil)',
            'en_ro': 'English → Romanian',
            'en_sk': 'English → Slovak',
            'en_sl': 'English → Slovenian',
            'en_es': 'English → Spanish',
            'en_sv': 'English → Swedish',
            'en_tl': 'English → Tagalog',
            'en_th': 'English → Thai',
            'en_tr': 'English → Turkish',
            'en_uk': 'English → Ukrainian',
            'en_ur': 'English → Urdu',
            'eo_en': 'Esperanto → English',
            'et_en': 'Estonian → English',
            'fi_en': 'Finnish → English',
            'gl_en': 'Galician → English',
            'el_en': 'Greek → English',
            'he_en': 'Hebrew → English',
            'hi_en': 'Hindi → English',
            'hu_en': 'Hungarian → English',
            'id_en': 'Indonesian → English',
            'ga_en': 'Irish → English',
            'ky_en': 'Kyrgyz → English',
            'lv_en': 'Latvian → English',
            'lt_en': 'Lithuanian → English',
            'ms_en': 'Malay → English',
            'nb_en': 'Norwegian Bokmal → English',
            'fa_en': 'Persian → English',
            'pl_en': 'Polish → English',
            'pb_en': 'Portuguese (Brazil) → English',
            'pt_en': 'Portuguese → English',
            'es_pt': 'Spanish → Portuguese',
            'ro_en': 'Romanian → English',
            'sk_en': 'Slovak → English',
            'sl_en': 'Slovenian → Spanish',
            'es_en': 'Spanish → English',
            'sv_en': 'Swedish → English',
            'tl_en': 'Tagalog → English',
            'th_en': 'Thai → English',
            'tr_en': 'Turkish → English',
            'uk_en': 'Ukrainian → English',
            'ur_en': 'Urdu → English',
        }

        translation_mapping = {
            'en_ru': TranslationPackage.EN_TO_RU,
            'ru_en': TranslationPackage.RU_TO_EN,
            'de_en': TranslationPackage.DE_TO_EN,
            'fr_en': TranslationPackage.FR_TO_EN,
            'it_en': TranslationPackage.IT_TO_EN,
            'ja_en': TranslationPackage.JA_TO_EN,
            'zh_en': TranslationPackage.ZH_TO_EN,
            'sq_en': TranslationPackage.SQ_TO_EN,
            'ar_en': TranslationPackage.AR_TO_EN,
            'az_en': TranslationPackage.AZ_TO_EN,
            'eu_en': TranslationPackage.EU_TO_EN,
            'bn_en': TranslationPackage.BN_TO_EN,
            'bg_en': TranslationPackage.BG_TO_EN,
            'ca_en': TranslationPackage.CA_TO_EN,
            'zt_en': TranslationPackage.ZT_TO_EN,
            'cs_en': TranslationPackage.CS_TO_EN,
            'da_en': TranslationPackage.DA_TO_EN,
            'nl_en': TranslationPackage.NL_TO_EN,
            'en_sq': TranslationPackage.EN_TO_SQ,
            'en_ar': TranslationPackage.EN_TO_AR,
            'en_az': TranslationPackage.EN_TO_AZ,
            'en_eu': TranslationPackage.EN_TO_EU,
            'en_bn': TranslationPackage.EN_TO_BN,
            'en_bg': TranslationPackage.EN_TO_BG,
            'en_ca': TranslationPackage.EN_TO_CA,
            'en_zh': TranslationPackage.EN_TO_ZH,
            'en_zt': TranslationPackage.EN_TO_ZT,
            'en_cs': TranslationPackage.EN_TO_CS,
            'en_da': TranslationPackage.EN_TO_DA,
            'en_nl': TranslationPackage.EN_TO_NL,
            'en_eo': TranslationPackage.EN_TO_EO,
            'en_et': TranslationPackage.EN_TO_ET,
            'en_fi': TranslationPackage.EN_TO_FI,
            'en_fr': TranslationPackage.EN_TO_FR,
            'en_gl': TranslationPackage.EN_TO_GL,
            'en_de': TranslationPackage.EN_TO_DE,
            'en_el': TranslationPackage.EN_TO_EL,
            'en_he': TranslationPackage.EN_TO_HE,
            'en_hi': TranslationPackage.EN_TO_HI,
            'en_hu': TranslationPackage.EN_TO_HU,
            'en_id': TranslationPackage.EN_TO_ID,
            'en_ga': TranslationPackage.EN_TO_GA,
            'en_it': TranslationPackage.EN_TO_IT,
            'en_ja': TranslationPackage.EN_TO_JA,
            'en_ko': TranslationPackage.EN_TO_KO,
            'en_lv': TranslationPackage.EN_TO_LV,
            'en_lt': TranslationPackage.EN_TO_LT,
            'en_ms': TranslationPackage.EN_TO_MS,
            'en_nb': TranslationPackage.EN_TO_NB,
            'en_fa': TranslationPackage.EN_TO_FA,
            'en_pl': TranslationPackage.EN_TO_PL,
            'en_pt': TranslationPackage.EN_TO_PT,
            'en_pb': TranslationPackage.EN_TO_PB,
            'en_ro': TranslationPackage.EN_TO_RO,
            'en_sk': TranslationPackage.EN_TO_SK,
            'en_sl': TranslationPackage.EN_TO_SL,
            'en_es': TranslationPackage.EN_TO_ES,
            'en_sv': TranslationPackage.EN_TO_SV,
            'en_tl': TranslationPackage.EN_TO_TL,
            'en_th': TranslationPackage.EN_TO_TH,
            'en_tr': TranslationPackage.EN_TO_TR,
            'en_uk': TranslationPackage.EN_TO_UK,
            'en_ur': TranslationPackage.EN_TO_UR,
            'eo_en': TranslationPackage.EO_TO_EN,
            'et_en': TranslationPackage.ET_TO_EN,
            'fi_en': TranslationPackage.FI_TO_EN,
            'gl_en': TranslationPackage.GL_TO_EN,
            'el_en': TranslationPackage.EL_TO_EN,
            'he_en': TranslationPackage.HE_TO_EN,
            'hi_en': TranslationPackage.HI_TO_EN,
            'hu_en': TranslationPackage.HU_TO_EN,
            'id_en': TranslationPackage.ID_TO_EN,
            'ga_en': TranslationPackage.GA_TO_EN,
            'lv_en': TranslationPackage.LV_TO_EN,
            'lt_en': TranslationPackage.LT_TO_EN,
            'ms_en': TranslationPackage.MS_TO_EN,
            'nb_en': TranslationPackage.NB_TO_EN,
            'fa_en': TranslationPackage.FA_TO_EN,
            'pl_en': TranslationPackage.PL_TO_EN,
            'pb_en': TranslationPackage.PB_TO_EN,
            'pt_en': TranslationPackage.PT_TO_EN,
            'es_pt': TranslationPackage.ES_TO_PT,
            'ro_en': TranslationPackage.RO_TO_EN,
            'sk_en': TranslationPackage.SK_TO_EN,
            'sl_en': TranslationPackage.SL_TO_EN,
            'es_en': TranslationPackage.ES_TO_EN,
            'sv_en': TranslationPackage.SV_TO_EN,
            'tl_en': TranslationPackage.TL_TO_EN,
            'th_en': TranslationPackage.TH_TO_EN,
            'tr_en': TranslationPackage.TR_TO_EN,
            'uk_en': TranslationPackage.UK_TO_EN,
            'ur_en': TranslationPackage.UR_TO_EN
        }

        def update_layout(layout):
            layout_key = 'main' if layout == self.lang_layout_main else 'settings'
            self.lang_buttons[layout_key].clear()

            # Clear the layout
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget and widget.parent() is not None:
                    widget.deleteLater()

            # Find available languages
            available_languages = []
            for language_pair, name in languages.items():
                package_patterns = [
                    os.path.join(
                        base_dir,
                        "AlyssumResources/models/argostranslate/data/argos-translate/packages",
                        f"translate-{language_pair}-*"
                    ),
                    os.path.join(
                        base_dir,
                        "AlyssumResources/models/argostranslate/data/argos-translate/packages",
                        f"{language_pair}"
                    )
                ]
                found = False
                for pattern in package_patterns:
                    if any(Path(p).is_dir() for p in glob.glob(pattern)):
                        found = True
                        break
                if found:
                    available_languages.append((language_pair, name))

            # Create buttons for available languages
            current_package = cfg.get(cfg.package).value
            for code, name in available_languages:
                lang_button = TransparentTogglePushButton(name)
                lang_button.setChecked(code == current_package)
                self.lang_buttons[layout_key][code] = lang_button

                def handler(checked=False, c=code):
                    # Uncheck all others
                    for btns in self.lang_buttons.values():
                        for other_code, other_btn in btns.items():
                            other_btn.setChecked(other_code == c)

                    cfg.set(cfg.package, translation_mapping[c])
                    self.card_settlpackage.setValue(translation_mapping[c])

                #lang_button.clicked.connect(lambda _, c=code: self.card_settlpackage.setValue(translation_mapping[c]))
                lang_button.clicked.connect(handler)
                layout.addWidget(lang_button, alignment=Qt.AlignmentFlag.AlignTop)

            # Show/hide the widget based on available languages
            if layout == self.lang_layout_main:
                self.lang_widget_main.setVisible(len(available_languages) > 0)
            else:
                self.lang_widget_settings.setVisible(len(available_languages) > 0)

        update_layout(self.lang_layout_main)
        update_layout(self.lang_layout_settings)


    def packageremover(self):
        language_pair = cfg.get(cfg.package).value

        package_patterns = [
            os.path.join(
                base_dir,
                "AlyssumResources/models/argostranslate/data/argos-translate/packages",
                f"translate-{language_pair}-*"
            ),
            os.path.join(
                base_dir,
                "AlyssumResources/models/argostranslate/data/argos-translate/packages",
                f"{language_pair}"
            )
        ]


        # Remove .argosmodel file
        model_file = os.path.join(
            base_dir,
            "AlyssumResources/models/argostranslate/cache/argos-translate/downloads",
            f"translate-{language_pair}.argosmodel"
        )

        try:
            # Remove matching package directories
            removed_dirs = False
            for pattern in package_patterns:
                for dir_path in glob.glob(pattern):
                    if os.path.isdir(dir_path):
                        shutil.rmtree(dir_path)
                        removed_dirs = True

            # Remove model file if exists
            removed_file = False
            if os.path.exists(model_file):
                os.remove(model_file)
                removed_file = True

            # Only update config if we actually removed something
            if removed_dirs or removed_file:
                cfg.set(cfg.package, 'None')
                self.check_packages()

                InfoBar.success(
                    title=QCoreApplication.translate("MainWindow", "Success"),
                    content=QCoreApplication.translate("MainWindow", "Translation package removed successfully"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
            else:
                InfoBar.warning(
                    title=QCoreApplication.translate("MainWindow", "Warning"),
                    content=QCoreApplication.translate("MainWindow", "No translation package found to remove"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )

        except Exception as e:
            InfoBar.error(
                title=QCoreApplication.translate("MainWindow", "Error"),
                content=QCoreApplication.translate("MainWindow", f"Failed to remove translation package: {str(e)}"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=2000,
                parent=self
            )

    def closeEvent(self, event):
        for widget in QApplication.topLevelWidgets():
            widget.close()

        super().closeEvent(event)

    def restartinfo(self):
        InfoBar.warning(
            title=(QCoreApplication.translate("MainWindow", "Success")),
            content=(QCoreApplication.translate("MainWindow", "Setting takes effect after restart")),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=2000,
            parent=self
        )

    @pyqtSlot()
    def start_translation_process(self):
        self.translator.start_translation(self.textinputw.toPlainText())

    @pyqtSlot()
    def start_ocr_process(self, pixmap):
        self.ocr.start_ocr_process(pixmap)

    def on_translation_done(self, result, success):
        if success:
            self.textoutputw.setPlainText(result)
        else:  # Error message
            self.textoutputw.setPlainText(f"Error translating:{result}")

        if hasattr(self.translator, 'translation_worker'):
            self.translator.translation_worker.abort()

    def on_ocr_done(self, extracted_text, success):
        if success:
            ct = self.clean_text(extracted_text)
            self.textinputw.setPlainText(ct)
            window.showNormal()
        else:
            InfoBar.error(
                title="Error",
                content=extracted_text,
                duration=200000,
                parent=self
            )

    def on_package_download_finished(self, status):
        if status == "start":
            self.download_progressbar.start()
            InfoBar.info(
                title=QCoreApplication.translate("MainWindow", "Information"),
                content=QCoreApplication.translate("MainWindow", "Downloading {} package").format(cfg.get(cfg.package).value),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
            )
            self.update_argos_remove_button_state(False)
        elif status == "success":
            self.download_progressbar.stop()
            InfoBar.success(
                title=QCoreApplication.translate("MainWindow", "Success"),
                content=QCoreApplication.translate("MainWindow", "Package installed successfully!"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
            )
            self.update_argos_remove_button_state(True)
            self.check_packages()
        elif status.startswith("error"):
            InfoBar.error(
                title=QCoreApplication.translate("MainWindow", "Error"),
                content=status,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
            )
            self.update_argos_remove_button_state(False)



if __name__ == "__main__":
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    if os.name == 'nt':
        import ctypes
        myappid = u'icosane.alyssum.translator.19'  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    app = QApplication(sys.argv)
    locale = cfg.get(cfg.language).value
    fluentTranslator = FluentTranslator(locale)
    appTranslator = QTranslator()
    lang_path = os.path.join(res_dir, "AlyssumResources", "lang")
    appTranslator.load(locale, "lang", ".", lang_path)

    app.installTranslator(fluentTranslator)
    app.installTranslator(appTranslator)

    window = MainWindow()
    window.show()
    sys.excepthook = ErrorHandler()
    sys.stderr = ErrorHandler()
    sys.exit(app.exec())
