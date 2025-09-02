import sys, os
from PyQt5.QtGui import QColor, QIcon, QFont, QPixmap, QPainter, QPen, QImage, QKeySequence
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QStackedWidget, QFileDialog, QSizePolicy, QSystemTrayIcon, QMenu
from PyQt5.QtCore import Qt, pyqtSignal, QTranslator, QCoreApplication, pyqtSlot, QRect, QTimer, QObject, QEvent, QSettings
sys.stdout = open(os.devnull, 'w')
import warnings
warnings.filterwarnings("ignore")
from qfluentwidgets import setThemeColor, TransparentToolButton, FluentIcon, PushSettingCard, isDarkTheme, MessageBox, FluentTranslator, IndeterminateProgressBar, PushButton, SubtitleLabel, ComboBoxSettingCard, OptionsSettingCard, HyperlinkCard, ScrollArea, InfoBar, InfoBarPosition, StrongBodyLabel, TransparentTogglePushButton, TextBrowser, TextEdit, BodyLabel, LineEdit, SimpleExpandGroupSettingCard, SwitchButton, ToolTipFilter, ToolTipPosition, SwitchSettingCard, ToolButton
from qframelesswindow.utils import getSystemAccentColor
from AlyssumResources.config import cfg, TranslationPackage, available_packages, available_models
from AlyssumResources.argos_utils import update_package
from AlyssumResources.translator import TextTranslator
from AlyssumResources.tesseract import OCR
from AlyssumResources.file_translator import FileTranslator
from AlyssumResources.translate_server import TranslateServer
from AlyssumResources.whisper_utils import update_model
from AlyssumResources.voice_input import VoiceController
from ctranslate2 import get_cuda_device_count
import shutil
import traceback
import glob
from pathlib import Path
import pyautogui, re, secrets

def get_lib_paths():
    if getattr(sys, 'frozen', False):  # Running inside PyInstaller
        base_dir = os.path.join(sys.prefix)
    else:  # Running inside a virtual environment
        base_dir = os.path.join(sys.prefix, "Lib", "site-packages")

    nvidia_base_libs = os.path.join(base_dir, "nvidia")

    if sys.platform == "win32":
        cuda_runtime = os.path.join(nvidia_base_libs, "cuda_runtime", "bin")
        cublas = os.path.join(nvidia_base_libs, "cublas", "bin")
        cudnn = os.path.join(nvidia_base_libs, "cudnn", "bin")
    else:
        cuda_runtime = os.path.join(nvidia_base_libs, "cuda_runtime", "lib")
        cublas = os.path.join(nvidia_base_libs, "cublas", "lib")
        cudnn = os.path.join(nvidia_base_libs, "cudnn", "lib")

    return [cuda_runtime, cublas, cudnn]


if get_cuda_device_count() != 0:
    for dll_path in get_lib_paths():
        if os.path.exists(dll_path):
            os.environ["PATH"] = dll_path + os.pathsep + os.environ["PATH"]


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

class ShortcutsCard(SimpleExpandGroupSettingCard):
    def __init__(self, parent=None):
        super().__init__(FluentIcon.TILES, QCoreApplication.translate("MainWindow", "Keyboard shortcuts"), QCoreApplication.translate("MainWindow", "Edit keyboard shortcuts"), parent)
        self.switchb = SwitchButton()
        self.addWidget(self.switchb)
        self.switchb.setChecked(cfg.get(cfg.shortcuts))
        self.switchb.checkedChanged.connect(self.shortcut_state)

        # First group
        self.modeButton0 = ShortcutEdit()
        self.modeLabel0 = BodyLabel(QCoreApplication.translate("MainWindow", "Configure OCR shortcut"))
        self.modeButton0.setFixedWidth(155)
        self.modeButton0.shortcutChanged.connect(self.updateOcrShortcut)
        ocr_shortcut = cfg.get(cfg.ocrcut).toString()
        self.modeButton0.setText(ocr_shortcut)

        # Second group
        self.modeButton1 = ShortcutEdit()
        self.modeLabel1 = BodyLabel(QCoreApplication.translate("MainWindow", "Configure translation shortcut"))
        self.modeButton1.setFixedWidth(155)
        self.modeButton1.shortcutChanged.connect(self.updateTranslationShortcut)
        tl_shortcut = cfg.get(cfg.tlcut).toString()
        self.modeButton1.setText(tl_shortcut)

        # Third group
        self.modeButton2 = ShortcutEdit()
        self.modeLabel2 = BodyLabel(QCoreApplication.translate("MainWindow", "Configure clear shortcut"))
        self.modeButton2.setFixedWidth(155)
        self.modeButton2.shortcutChanged.connect(self.updateClearShortcut)
        cl_shortcut = cfg.get(cfg.clcut).toString()
        self.modeButton2.setText(cl_shortcut)

        # Forth group
        self.modeButton3 = ShortcutEdit()
        self.modeLabel3 = BodyLabel(QCoreApplication.translate("MainWindow", "Configure copy shortcut"))
        self.modeButton3.setFixedWidth(155)
        self.modeButton3.shortcutChanged.connect(self.updateCopyShortcut)
        select_and_copy_shortcut = cfg.get(cfg.copycut).toString()
        self.modeButton3.setText(select_and_copy_shortcut)

        # Fifth group
        self.modeButton4 = ShortcutEdit()
        self.modeLabel4 = BodyLabel(QCoreApplication.translate("MainWindow", "Configure file translator shortcut"))
        self.modeButton4.setFixedWidth(155)
        self.modeButton4.shortcutChanged.connect(self.updateFileShortcut)
        file_shortcut = cfg.get(cfg.filecut).toString()
        self.modeButton4.setText(file_shortcut)

        # Sixth group
        self.modeButton5 = ShortcutEdit()
        self.modeLabel5 = BodyLabel(QCoreApplication.translate("MainWindow", "Configure voice input shortcut"))
        self.modeButton5.setFixedWidth(155)
        self.modeButton5.shortcutChanged.connect(self.updateVoiceShortcut)
        voice_shortcut = cfg.get(cfg.startvi).toString()
        self.modeButton5.setText(voice_shortcut)

        # Adjust the internal layout
        self.viewLayout.setContentsMargins(0, 0, 0, 0)
        self.viewLayout.setSpacing(0)

        # Add each group to the setting card
        self.add(self.modeLabel0, self.modeButton0)
        self.add(self.modeLabel1, self.modeButton1)
        self.add(self.modeLabel2, self.modeButton2)
        self.add(self.modeLabel3, self.modeButton3)
        self.add(self.modeLabel4, self.modeButton4)
        self.add(self.modeLabel5, self.modeButton5)

    def add(self, label, widget):
        w = QWidget()
        w.setFixedHeight(60)

        layout = QHBoxLayout(w)
        layout.setContentsMargins(48, 12, 48, 12)

        layout.addWidget(label)
        layout.addStretch(1)
        layout.addWidget(widget)

        # Add the widget group to the setting card
        self.addGroupWidget(w)

    def shortcut_state(self):
        cfg.set(cfg.shortcuts, self.switchb.isChecked())

    def updateOcrShortcut(self, key, modifiers):
        shortcut_str = self._modifiers_to_string(key, modifiers)
        shortcut = QKeySequence(shortcut_str)
        cfg.set(cfg.ocrcut, shortcut)

    def updateTranslationShortcut(self, key, modifiers):
        shortcut_str = self._modifiers_to_string(key, modifiers)
        shortcut = QKeySequence(shortcut_str)
        cfg.set(cfg.tlcut, shortcut)

    def updateClearShortcut(self, key, modifiers):
        shortcut_str = self._modifiers_to_string(key, modifiers)
        shortcut = QKeySequence(shortcut_str)
        cfg.set(cfg.clcut, shortcut)

    def updateCopyShortcut(self, key, modifiers):
        shortcut_str = self._modifiers_to_string(key, modifiers)
        shortcut = QKeySequence(shortcut_str)
        cfg.set(cfg.copycut, shortcut)

    def updateFileShortcut(self, key, modifiers):
        shortcut_str = self._modifiers_to_string(key, modifiers)
        shortcut = QKeySequence(shortcut_str)
        cfg.set(cfg.filecut, shortcut)

    def updateVoiceShortcut(self, key, modifiers):
        shortcut_str = self._modifiers_to_string(key, modifiers)
        shortcut = QKeySequence(shortcut_str)
        cfg.set(cfg.startvi, shortcut)

    def _modifiers_to_string(self, key, modifiers):
        names = []

        if Qt.ControlModifier in modifiers:
            names.append("Ctrl")
        if Qt.ShiftModifier in modifiers:
            names.append("Shift")
        if Qt.AltModifier in modifiers:
            names.append("Alt")
        if Qt.MetaModifier in modifiers:
            names.append("Meta")

        if key != 0:
            names.append(QKeySequence(key).toString())

        return "+".join(names)


    def set_ocr_shortcut(self, shortcut):
        self.modeButton0.setText(shortcut.toString())

    def set_translation_shortcut(self, shortcut):
        self.modeButton1.setText(shortcut.toString())

    def set_clear_shortcut(self, shortcut):
        self.modeButton2.setText(shortcut.toString())

    def set_copy_shortcut(self, shortcut):
        self.modeButton3.setText(shortcut.toString())

    def set_file_shortcut(self, shortcut):
        self.modeButton4.setText(shortcut.toString())

    def set_voice_shortcut(self, shortcut):
        self.modeButton5.setText(shortcut.toString())

class ShortcutEdit(LineEdit):
    shortcutChanged = pyqtSignal(int, list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setReadOnly(True)
        self.current_key = 0
        self.current_modifiers = []

    def event(self, event):
        if event.type() == QEvent.KeyPress:
            # Reset current state
            self.current_key = 0
            self.current_modifiers = []

            key = event.key()
            mods = event.modifiers()

            # Ignore pure modifier key presses
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return True

            if key == Qt.Key_Space and not mods:
                return True

            self.current_key = key

            if mods & Qt.ControlModifier:
                self.current_modifiers.append(Qt.ControlModifier)
            if mods & Qt.ShiftModifier:
                self.current_modifiers.append(Qt.ShiftModifier)
            if mods & Qt.AltModifier:
                self.current_modifiers.append(Qt.AltModifier)
            if mods & Qt.MetaModifier:
                self.current_modifiers.append(Qt.MetaModifier)

            # Create key sequence
            combo_int = int(mods) | key
            key_seq = QKeySequence(combo_int)
            self.setText(key_seq.toString())

            self.shortcutChanged.emit(self.current_key, self.current_modifiers)
            return True

        return super().event(event)


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
        self.setCursor(Qt.CrossCursor)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Semi-transparent dark overlay
        if not self.selection_rect:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 100))


        if self.selection_rect:
            # Set up a transparent brush and red pen
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)

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
            self.setCursor(Qt.ArrowCursor)

            # Correctly calculate coordinates
            x1 = min(self.start_point.x(), self.end_point.x())
            y1 = min(self.start_point.y(), self.end_point.y())
            x2 = max(self.start_point.x(), self.end_point.x())
            y2 = max(self.start_point.y(), self.end_point.y())

            width = x2 - x1
            height = y2 - y1

            # Only capture if selection is larger than a few pixels
            if width > 5 and height > 5:
                # Capture the actual screen region
                #screenshot = pyautogui.screenshot(region=(x1, y1, width, height))
                scale = float(os.environ.get("QT_SCALE_FACTOR", "1"))
                scaled_x = int(x1 * scale)
                scaled_y = int(y1 * scale)
                scaled_w = int(width * scale)
                scaled_h = int(height * scale)

                screenshot = pyautogui.screenshot(region=(scaled_x, scaled_y, scaled_w, scaled_h))

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
        self.screenshot_taken.emit(pixmap)


class PlainTextEdit(TextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptRichText(False)
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
            pass

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
    whispermodel_changed = pyqtSignal()
    lang_changed = pyqtSignal()
    fileSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle(QCoreApplication.translate("MainWindow", "Alyssum"))
        icon_path = os.path.join(res_dir, "AlyssumResources", "assets", "icon.ico")
        if not os.path.exists(icon_path) and sys.platform != "win32":
            icon_path = os.path.join(res_dir, "AlyssumResources", "assets", "icon.png")
        self.setWindowIcon(QIcon(icon_path))
        self.settings = QSettings('icosane', 'Alyssum')
        self.setMinimumSize(800,900)
        self._local_api_key = self.settings.value("key", type=str)
        if not self._local_api_key:
            self._local_api_key = secrets.token_urlsafe(16)
            self.settings.setValue("key", self._local_api_key)
        self.restore_settings()
        self.last_directory = ""
        self.current_text = ""
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        self.lang_buttons = {
            'main': {},
            'settings': {}
        }

        self.server_thread = None

        self.scroll_area_main = ScrollArea()
        self.scroll_area_main.setWidgetResizable(True)
        self.scroll_area_main.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area_main.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area_main.setFixedHeight(50)

        self.scroll_area_settings = ScrollArea()
        self.scroll_area_settings.setWidgetResizable(True)
        self.scroll_area_settings.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area_settings.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area_settings.setFixedHeight(50)

        self.lang_layout_main = QHBoxLayout()
        self.lang_widget_main = QWidget()
        self.lang_widget_main.setLayout(self.lang_layout_main)
        self.lang_layout_main.addStretch()
        self.lang_layout_settings = QHBoxLayout()
        self.lang_widget_settings = QWidget()
        self.lang_widget_settings.setLayout(self.lang_layout_settings)
        self.lang_layout_settings.addStretch()

        self.voice_controller = VoiceController(
            whisper_model_name=cfg.get(cfg.whisper_model).value,
            device="cuda" if get_cuda_device_count() > 0 else "cpu"
        )

        self.main_layout()
        self.settings_layout()
        self.setup_theme()
        update_model(self)
        self.center()
        self.startserver()

        self.theme_changed.connect(self.update_theme)
        self.package_changed.connect(lambda: update_package(self))
        self.lang_changed.connect(self.on_lang_change)
        self.whispermodel_changed.connect(lambda: update_model(self))

        self.translator = TextTranslator(self, cfg)
        self.screenshot_tool = ScreenshotTool(parent=self)
        self.screenshot_tool.screenshot_taken.connect(self.on_screenshot_taken)
        self.ocr = OCR(self, cfg)
        self.file_translator = FileTranslator(self, cfg)
        cfg.ocrcut.valueChanged.connect(self.update_ocr_shortcut)
        cfg.tlcut.valueChanged.connect(self.update_translation_shortcut)
        cfg.clcut.valueChanged.connect(self.update_clear_shortcut)
        cfg.copycut.valueChanged.connect(self.update_copy_shortcut)

        self.setup_tray_icon()
        self.installEventFilter(self)

    def setup_theme(self):
        if sys.platform in ["win32", "darwin"]:
            setThemeColor(getSystemAccentColor())
        else:
            setThemeColor(QColor("#FFFFFF"))
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

    def get_tray_menu_stylesheet(self, is_dark_theme):
        if is_dark_theme:
            # White text on dark menu background
            return """
            QMenu {
                background-color: #2d2d2d;
                color: white;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            """
        else:
            # Dark text on light menu background
            return """
            QMenu {
                background-color: #f0f0f0;
                color: black;
            }
            QMenu::item:selected {
                background-color: #d0d0d0;
            }
            """

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
            InfoBar.warning(
                title="Warning",
                content="No valid screenshot captured.",
                duration=2000,
                parent=self
            )

    def on_lang_change(self):
        self.ocr.set_package(cfg.package)
        if hasattr(self, "lang_menu_widget"):
            self.populate_language_submenu(self.lang_menu_widget)

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

        self.scroll_area_main.setWidget(self.lang_widget_main)
        main_layout.addWidget(self.scroll_area_main)
        self.check_packages()

        font = QFont()
        font.setPointSize(14)
        self.textinputw = PlainTextEdit()
        self.textinputw.setFont(font)
        main_layout.addWidget(self.textinputw)

        self.mic_button = ToolButton(FluentIcon.MICROPHONE)
        button_layout.addWidget(self.mic_button)
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
        self.file_button = TransparentToolButton(FluentIcon.FOLDER)

        settings_layout = QHBoxLayout()
        settings_layout.addWidget(self.settings_button)
        settings_layout.addWidget(self.copy_button)
        settings_layout.addWidget(self.ocr_button)
        settings_layout.addWidget(self.file_button)
        settings_layout.addStretch()
        settings_layout.setContentsMargins(5, 5, 5, 5)

        self.progressbar = IndeterminateProgressBar(start=False)
        main_layout.addWidget(self.progressbar)

        main_layout.addLayout(settings_layout)

        #tooltips
        self.settings_button.setToolTip(QCoreApplication.translate("MainWindow", "Settings"))
        self.settings_button.setToolTipDuration(2000)
        self.settings_button.installEventFilter(ToolTipFilter(self.settings_button, 0, ToolTipPosition.TOP))

        self.copy_button.setToolTip(QCoreApplication.translate("MainWindow", "Copy to clipboard"))
        self.copy_button.setToolTipDuration(2000)
        self.copy_button.installEventFilter(ToolTipFilter(self.copy_button, 0, ToolTipPosition.TOP))

        self.ocr_button.setToolTip(QCoreApplication.translate("MainWindow", "Start OCR"))
        self.ocr_button.setToolTipDuration(2000)
        self.ocr_button.installEventFilter(ToolTipFilter(self.ocr_button, 0, ToolTipPosition.TOP))

        self.file_button.setToolTip(QCoreApplication.translate("MainWindow", "Open file picker"))
        self.file_button.setToolTipDuration(2000)
        self.file_button.installEventFilter(ToolTipFilter(self.file_button, 0, ToolTipPosition.TOP))

        #connect
        self.settings_button.clicked.connect(self.show_settings_page)
        self.copy_button.clicked.connect(self.selectandcopy)
        self.ocr_button.clicked.connect(self.screenshot_start)
        self.tl_button.clicked.connect(self.start_translation_process)
        self.cl_button.clicked.connect(self.clearinpoutw)
        self.file_button.clicked.connect(self.start_file_translation)
        self.mic_button.clicked.connect(self.voice_controller.toggle_recording)
        self.voice_controller.recording_started.connect(self._on_recording_started)
        self.voice_controller.recording_stopped.connect(self._on_recording_stopped)
        self.voice_controller.transcription_ready.connect(self.on_transcription_ready)

        self.voice_controller.recording_started.connect(
            lambda: self.textinputw.setPlaceholderText(
                (QCoreApplication.translate("MainWindow","Recording...") if self.voice_controller.model else (QCoreApplication.translate("MainWindow","Loading Whisper model...")))
            )
        )
        self.voice_controller.recording_stopped.connect(
            lambda: self.textinputw.setPlaceholderText(QCoreApplication.translate("MainWindow","Transcribing..."))
        )
        self.voice_controller.transcription_ready.connect(self.on_transcription_ready)


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
            texts=['None',
                *[self.languages.get(f"{pkg.from_code}_{pkg.to_code}", f"{pkg.from_code} → {pkg.to_code}") for pkg in available_packages]
            ]


        )

        card_layout.addWidget(self.card_settlpackage, alignment=Qt.AlignmentFlag.AlignTop)
        cfg.package.valueChanged.connect(self.package_changed.emit)
        cfg.package.valueChanged.connect(self.lang_changed.emit)

        self.scroll_area_settings.setWidget(self.lang_widget_settings)
        card_layout.addWidget(self.scroll_area_settings)
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

        card_layout.addSpacing(20)
        self.card_setwhispermodel = ComboBoxSettingCard(
            configItem=cfg.whisper_model,
            icon=FluentIcon.CLOUD_DOWNLOAD,
            title=QCoreApplication.translate("MainWindow","Whisper Model"),
            content=QCoreApplication.translate("MainWindow", "Change speech recognition model"),
            texts=['None',
                *[m for m in available_models() if not m.startswith('distil') and not m.endswith('.en') and m != 'turbo']]
        )

        card_layout.addWidget(self.card_setwhispermodel, alignment=Qt.AlignmentFlag.AlignTop)
        cfg.whisper_model.valueChanged.connect(self.whispermodel_changed.emit)

        self.card_deletewhispermodel = PushSettingCard(
            text=QCoreApplication.translate("MainWindow","Remove"),
            icon=FluentIcon.BROOM,
            title=QCoreApplication.translate("MainWindow","Remove Whisper model"),
            content=QCoreApplication.translate("MainWindow", "Delete currently selected speech-to-text model. Will be removed: <b>{}</b>").format(cfg.get(cfg.whisper_model).value),
        )

        card_layout.addWidget(self.card_deletewhispermodel, alignment=Qt.AlignmentFlag.AlignTop)
        self.card_deletewhispermodel.clicked.connect(self.whispermodelremover)
        if ((cfg.get(cfg.whisper_model).value == 'None')):
            self.card_deletewhispermodel.button.setDisabled(True)

        self.miscellaneous_title = StrongBodyLabel(QCoreApplication.translate("MainWindow", "Miscellaneous"))
        self.miscellaneous_title.setTextColor(QColor(0, 0, 0), QColor(255, 255, 255))
        card_layout.addSpacing(20)
        card_layout.addWidget(self.miscellaneous_title, alignment=Qt.AlignmentFlag.AlignTop)

        self.card_editshortcuts = ShortcutsCard()
        card_layout.addWidget(self.card_editshortcuts, alignment=Qt.AlignmentFlag.AlignTop)

        self.card_enabletray = SwitchSettingCard(
            icon=FluentIcon.TRANSPARENT,
            title=QCoreApplication.translate("MainWindow","Enable Browser extension"),
            content=QCoreApplication.translate("MainWindow","Integrates with the web browser and alters the way the app minimizes to the system tray instead of the taskbar."),
            configItem=cfg.tray
        )
        card_layout.addWidget(self.card_enabletray, alignment=Qt.AlignmentFlag.AlignTop)
        cfg.tray.valueChanged.connect(self.startserver)

        self.card_apikey = PushSettingCard(
            text=QCoreApplication.translate("MainWindow","Copy"),
            icon=FluentIcon.COPY,
            title=QCoreApplication.translate("MainWindow","API key"),
            content=""
        )
        card_layout.addWidget(self.card_apikey, alignment=Qt.AlignmentFlag.AlignTop)
        self.card_apikey.clicked.connect(self.get_translate_server_key)

        self.card_switch_line_format = SwitchSettingCard(
            icon=FluentIcon.FONT_SIZE,
            title=QCoreApplication.translate("MainWindow","Voice-to-text output format"),
            content=QCoreApplication.translate("MainWindow","Click to toggle between continuous text and lines per sentence."),
            configItem=cfg.lineformat
        )

        card_layout.addWidget(self.card_switch_line_format, alignment=Qt.AlignmentFlag.AlignTop)

        self.card_setlanguage = ComboBoxSettingCard(
            configItem=cfg.language,
            icon=FluentIcon.LANGUAGE,
            title=QCoreApplication.translate("MainWindow","Language"),
            content=QCoreApplication.translate("MainWindow", "Change UI language"),
            texts=["English", "Русский", "Deutsch"]
        )

        card_layout.addWidget(self.card_setlanguage, alignment=Qt.AlignmentFlag.AlignTop)
        cfg.language.valueChanged.connect(self.restartinfo)

        self.card_theme = OptionsSettingCard(
            cfg.themeMode,
            FluentIcon.BRUSH,
            QCoreApplication.translate("MainWindow","Application theme"),
            QCoreApplication.translate("MainWindow", "Adjust appearance"),
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
            content=QCoreApplication.translate("MainWindow", "Offline translator with OCR, voice input, and file/book translation.\nThis software contains source code provided by NVIDIA Corporation. Licenses and details are on GitHub.")
        )
        card_layout.addWidget(self.card_ab,  alignment=Qt.AlignmentFlag.AlignTop )

        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.card_widget = QWidget()
        self.card_widget.setLayout(card_layout)
        self.card_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
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
        empty = not self.textoutputw.toPlainText().strip()

        if empty:
            InfoBar.info(
                title=QCoreApplication.translate("MainWindow", "Information"),
                content=QCoreApplication.translate("MainWindow", "Nothing to copy"),
                orient=Qt.Orientation.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM,
                duration=4000,
                parent=self
            )
        else:
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
        if cfg.get(cfg.shortcuts):
            pressed = QKeySequence(int(event.modifiers()) | event.key())

            if pressed.matches(cfg.get(cfg.ocrcut)) == QKeySequence.ExactMatch:
                self.screenshot_start()
            elif pressed.matches(cfg.get(cfg.tlcut)) == QKeySequence.ExactMatch:
                self.tl_button.click()
            elif pressed.matches(cfg.get(cfg.clcut)) == QKeySequence.ExactMatch:
                self.cl_button.click()
            elif pressed.matches(cfg.get(cfg.copycut)) == QKeySequence.ExactMatch:
                self.selectandcopy()
            elif pressed.matches(cfg.get(cfg.filecut)) == QKeySequence.ExactMatch:
                self.start_file_translation()
            elif pressed.matches(cfg.get(cfg.startvi)) == QKeySequence.ExactMatch:
                self.voice_controller.toggle_recording()

        super().keyPressEvent(event)


    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(os.path.join(res_dir, "AlyssumResources", "assets", "icon.ico")))
        self.tray_icon.setToolTip("Alyssum")

        # Tray menu
        self.tray_menu = QMenu(self)
        self.tray_menu.setStyleSheet(self.get_tray_menu_stylesheet(isDarkTheme()))

        # Show / Restore
        show_action = self.tray_menu.addAction(QCoreApplication.translate("MainWindow", "Show"))
        show_action.triggered.connect(self.show_window_from_tray)

        # OCR shortcut
        ocr_action = self.tray_menu.addAction(QCoreApplication.translate("MainWindow", "Start OCR"))
        ocr_action.triggered.connect(self.screenshot_start)

        # Store both the menu and the dict of actions
        self.lang_menu_widget = self.tray_menu.addMenu(QCoreApplication.translate("MainWindow", "Language package"))
        self.lang_menu_actions = {}

        self.populate_language_submenu(self.lang_menu_widget)

        # Quit
        quit_action = self.tray_menu.addAction(QCoreApplication.translate("MainWindow", "Quit"))
        quit_action.triggered.connect(QApplication.instance().quit)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.setVisible(False)


    def populate_language_submenu(self, menu: QMenu):
        menu.clear()
        self.lang_menu_actions.clear()

        current_package = cfg.get(cfg.package).value

        for code, name in self.available_languages:
            act = menu.addAction(name)
            act.setCheckable(True)
            act.setChecked(code == current_package)
            self.lang_menu_actions[code] = act

            def handler(checked=False, c=code):
                # Uncheck all others
                for other_code, other_act in self.lang_menu_actions.items():
                    other_act.setChecked(other_code == c)

                for layout_key, btn_dict in self.lang_buttons.items():
                    for other_code, btn in btn_dict.items():
                        btn.setChecked(other_code == c)

                cfg.set(cfg.package, self.translation_mapping[c])
                self.card_settlpackage.setValue(self.translation_mapping[c])

            act.triggered.connect(handler)

    def on_tray_icon_activated(self, reason):
        # Respond to left-click or double-click
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.show_window_from_tray()

    def show_window_from_tray(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()
        self.tray_icon.setVisible(False)

    def eventFilter(self, obj, event):
        if obj is self and event.type() == QEvent.Close:
            if cfg.get(cfg.tray) is True:
                event.ignore()
                self.hide()
                self.tray_icon.setVisible(True)
        return super().eventFilter(obj, event)



    def check_packages(self):

        self.languages = {f"{pkg.from_code}_{pkg.to_code}": f"{pkg}" for pkg in available_packages}

        self.translation_mapping = {f"{pkg.from_code}_{pkg.to_code}": getattr(TranslationPackage, f"{pkg.from_code.upper()}_TO_{pkg.to_code.upper()}", None) for pkg in available_packages}

        def update_layout(layout):
            layout_key = 'main' if layout == self.lang_layout_main else 'settings'
            self.lang_buttons[layout_key].clear()

            # Clear the layout
            for i in reversed(range(layout.count())):
                widget = layout.itemAt(i).widget()
                if widget and widget.parent() is not None:
                    widget.deleteLater()

            # Find available languages
            self.available_languages = []
            for language_pair, name in self.languages.items():
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
                    self.available_languages.append((language_pair, name))

            # Create buttons for available languages
            current_package = cfg.get(cfg.package).value
            for code, name in self.available_languages:
                lang_button = TransparentTogglePushButton(name)
                lang_button.setChecked(code == current_package)
                self.lang_buttons[layout_key][code] = lang_button

                def handler(checked=False, c=code):
                    # Uncheck all others
                    for btns in self.lang_buttons.values():
                        for other_code, other_btn in btns.items():
                            other_btn.setChecked(other_code == c)

                    cfg.set(cfg.package, self.translation_mapping[c])
                    self.card_settlpackage.setValue(self.translation_mapping[c])

                lang_button.clicked.connect(handler)
                layout.addWidget(lang_button, alignment=Qt.AlignmentFlag.AlignTop)

            # Show/hide the widget based on available languages
            if layout == self.lang_layout_main:
                self.scroll_area_main.setVisible(len(self.available_languages) > 0)
            else:
                self.scroll_area_settings.setVisible(len(self.available_languages) > 0)

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

    def whispermodelremover(self):
        directory = os.path.join(base_dir, "AlyssumResources", "models", "whisper", f"models--Systran--faster-whisper-{cfg.get(cfg.whisper_model).value}")
        if not os.path.exists(directory):
            directory = os.path.join(base_dir, "AlyssumResources", "models", "whisper", f"models--mobiuslabsgmbh--faster-whisper-{cfg.get(cfg.whisper_model).value}")
        if os.path.exists(directory) and os.path.isdir(directory):
            try:
                # Remove the directory and its contents
                shutil.rmtree(directory)
                cfg.set(cfg.whisper_model, 'None')


                InfoBar.success(
                    title=QCoreApplication.translate("MainWindow", "Success"),
                    content=QCoreApplication.translate("MainWindow", "Whisper Model removed"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    title=QCoreApplication.translate("MainWindow", "Error"),
                    content=QCoreApplication.translate("MainWindow", f"Failed to remove Whisper model: {e}"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=2000,
                    parent=self
                )

    def closeEvent(self, event):
        if cfg.get(cfg.tray) is True:
            event.ignore()
            self.hide()
            self.tray_icon.setVisible(True)
        else:
            for widget in QApplication.topLevelWidgets():
                widget.close()

            self.save_settings()

            super().closeEvent(event)

    def save_settings(self):
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("key", self._local_api_key)

    def restore_settings(self):
        size = self.settings.value("size")
        pos = self.settings.value("pos")

        if size is not None:
            self.resize(size)
        if pos is not None:
            self.move(pos)

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

    def startserver(self):
        if cfg.get(cfg.tray) is True:
            self.start_translate_server()
            self.server_thread.requestTranslation.connect(self.request_translation_in_main_thread)
        else:
            self.stop_translate_server()

    def request_translation_in_main_thread(self, text):
        self.textinputw.setPlainText(text)
        self.start_translation_process()

    def wheelEvent(self, event):
        self.scroll_area_main.horizontalScrollBar().setValue(
            self.scroll_area_main.horizontalScrollBar().value() - event.angleDelta().y()
        )
        self.scroll_area_settings.horizontalScrollBar().setValue(
            self.scroll_area_settings.horizontalScrollBar().value() - event.angleDelta().y()
        )

    def update_ocr_shortcut(self, shortcut):
        self.card_editshortcuts.set_ocr_shortcut(shortcut)

    def update_translation_shortcut(self, shortcut):
        self.card_editshortcuts.set_translation_shortcut(shortcut)

    def update_clear_shortcut(self, shortcut):
        self.card_editshortcuts.set_clear_shortcut(shortcut)

    def update_copy_shortcut(self, shortcut):
        self.card_editshortcuts.set_copy_shortcut(shortcut)

    def update_file_shortcut(self, shortcut):
        self.card_editshortcuts.set_file_shortcut(shortcut)

    def update_voice_shortcut(self, shortcut):
        self.card_editshortcuts.set_voice_shortcut(shortcut)

    def update_remove_button(self, enabled):
        if hasattr(self, 'card_deletewhispermodel'):
            self.card_deletewhispermodel.button.setEnabled(enabled)

    def update_record_button(self, enabled):
        if hasattr(self, 'mic_button'):
            self.mic_button.setEnabled(enabled)
            self.mic_button.repaint()

    def open_file_dialog(self):
        initial_dir = self.last_directory if self.last_directory else ""

        self.file_path, _ = QFileDialog.getOpenFileName(
            self,
            QCoreApplication.translate("MainWindow", "Select file"),
            initial_dir,
            QCoreApplication.translate("MainWindow",
                "Text files (*.pdf *.epub *.docx *.txt);;"
                "All Files (*)")
        )
        if self.file_path:
            self.last_directory = os.path.dirname(self.file_path)
            if self.is_document(self.file_path):
                self.fileSelected.emit(self.file_path)
            elif self.is_not_supported_document(self.file_path):
                InfoBar.error(
                    title=QCoreApplication.translate("MainWindow", "Error"),
                    content=QCoreApplication.translate("MainWindow", "File format not fully supported. Convert to .docx and try again."),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM,
                    duration=4000,
                    parent=window
                )
            else:
                InfoBar.error(
                    title=QCoreApplication.translate("MainWindow", "Error"),
                    content=QCoreApplication.translate("MainWindow", "Dropped file is not supported"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM,
                    duration=4000,
                    parent=window
                )

    def is_document(self, file_path):
        file_extensions = ['.pdf', '.epub', '.docx', '.txt', '.odp', '.pptx', '.srt', '.odt', '.html']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in file_extensions

    def is_not_supported_document(self, file_path):
        file_extensions = ['.doc', '.rtf']
        _, ext = os.path.splitext(file_path)
        return ext.lower() in file_extensions

    def on_file_translation_done(self, result, success):
        self.progressbar.stop()

        if success:
            InfoBar.success(
                title=QCoreApplication.translate('MainWindow',"Success"),
                content=QCoreApplication.translate('MainWindow', "Translated file saved to {}").format(result),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=4000,
                parent=self
            )
        elif result:
            InfoBar.error(
                title=QCoreApplication.translate('MainWindow',"Error"),
                content=result,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=4000,
                parent=self
            )

        if hasattr(self.file_translator, 'translation_worker'):
            self.file_translator.translation_worker.abort()

    @pyqtSlot()
    def start_translation_process(self):
        self.translator.start_translation(self.textinputw.toPlainText())

    @pyqtSlot()
    def start_file_translation(self):
        self.open_file_dialog()
        self.file_translator.start_translation(self.file_path)

    @pyqtSlot()
    def start_ocr_process(self, pixmap):
        self.ocr.start_ocr_process(pixmap)

    def start_translate_server(self):
        if self.server_thread and self.server_thread.isRunning():
            return
        self.server_thread = TranslateServer(self, api_key=self._local_api_key)
        self.server_thread.start()

    def stop_translate_server(self):
        if self.server_thread and self.server_thread.isRunning():
            self.server_thread.stop()
            self.server_thread.wait()

    def get_translate_server_key(self):
        """Expose API key so you can display it in Settings UI."""
        if self.server_thread:
            api_key = self.server_thread.get_api_key()
        else:
            api_key = self._local_api_key

        clipboard = app.clipboard()
        clipboard.setText(api_key)

        return api_key

    def on_translation_done(self, result, success):
        if success:
            self.textoutputw.setPlainText(result)
        else:
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

    def _on_mic_button_clicked(self):
        self.voice_controller.toggle_recording()

    def _on_recording_started(self):
        self.current_text = self.textinputw.toPlainText()
        self.clearinpoutw()
        if self.voice_controller.model:
            self.textinputw.setPlaceholderText(QCoreApplication.translate("MainWindow","Recording..."))
        else:
            self.textinputw.setPlaceholderText(QCoreApplication.translate("MainWindow","Loading Whisper model..."))
        self.mic_button.setIcon(FluentIcon.PAUSE)

    def _on_recording_stopped(self):
        self.textinputw.setPlaceholderText(QCoreApplication.translate("MainWindow","Transcribing..."))

    def on_transcription_ready(self, text):
        if (cfg.get(cfg.lineformat) is True):
            final = (self.current_text + '\n' + '\n' + text) if self.current_text else text  # start with new line
        else:
            final = (self.current_text + ' ' + text) if self.current_text else text  # default
        self.textinputw.setPlainText(final)
        self.textinputw.setPlaceholderText("")  # clear placeholder
        # Restore mic icon
        self.mic_button.setIcon(FluentIcon.MICROPHONE)



    def on_whispermodel_download_finished(self, status):
        if status == "start":
            self.download_progressbar.start()
            InfoBar.info(
                title=QCoreApplication.translate("MainWindow", "Information"),
                content=QCoreApplication.translate("MainWindow", "Downloading {} model").format(cfg.get(cfg.whisper_model).value),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
            )
            self.update_remove_button(False)

        elif status == "success":
            if hasattr(self, 'model_thread') and self.model_thread.isRunning():
                self.model_thread.stop()  # Stop the thread after success
            self.download_progressbar.stop()
            InfoBar.success(
                title=QCoreApplication.translate("MainWindow", "Success"),
                content=QCoreApplication.translate("MainWindow", "{} model installed successfully!").format(cfg.get(cfg.whisper_model).value),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self
            )
            self.update_remove_button(True)

        else:
            InfoBar.error(
                title=QCoreApplication.translate("MainWindow", "Error"),
                content=QCoreApplication.translate("MainWindow", f"Failed to download Whisper model: {status}"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM,
                duration=4000,
                parent=self
            )
            self.update_remove_button(False)

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
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
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
