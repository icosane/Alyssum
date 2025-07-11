from PyQt5.QtCore import QThread, pyqtSignal, QCoreApplication
from AlyssumResources.config import cfg
import argostranslate.package
import argostranslate.translate


class PackageDownloaderThread(QThread):
    download_finished = pyqtSignal(str)
    download_start = pyqtSignal(str)

    def __init__(self, from_code: str, to_code: str):
        super().__init__()
        self.from_code = from_code
        self.to_code = to_code
        self._stopped = False

    def run(self):
        try:
            self.download_start.emit("start")

            available_packages = argostranslate.package.get_available_packages()

            package = next(
                (p for p in available_packages
                 if p.from_code == self.from_code and p.to_code == self.to_code),
                None
            )

            if not package:
                self.download_finished.emit(f"error: Package {self.from_code}→{self.to_code} not found")
                return

            package_path = package.download()

            argostranslate.package.install_from_path(package_path)

            if self._stopped:
                self.download_finished.emit("cancelled")
            else:
                self.download_finished.emit("success")

        except Exception as e:
            self.download_finished.emit(f"error: {str(e)}")

    def stop(self):
        self._stopped = True
        self.quit()
        self.wait()

def package_downloader(main_window, from_lang: str, to_lang: str):
    """Check if package is installed and download if needed"""
    installed_languages = argostranslate.translate.get_installed_languages()

    # Check if translation is already available
    from_lang_obj = next((lg for lg in installed_languages if lg.code == from_lang), None)
    to_lang_obj = next((lg for lg in installed_languages if lg.code == to_lang), None)

    if from_lang_obj and to_lang_obj:
        try:
            if from_lang_obj.get_translation(to_lang_obj):
                return True  # Package already installed
        except:
            pass

    # Start download thread if needed
    if hasattr(main_window, 'package_thread') and main_window.package_thread.isRunning():
        main_window.package_thread.stop()

    main_window.package_thread = PackageDownloaderThread(from_lang, to_lang)
    main_window.package_thread.download_start.connect(main_window.on_package_download_finished)
    main_window.package_thread.download_finished.connect(main_window.on_package_download_finished)
    main_window.package_thread.start()

    return False

def update_package(main_window):
    language_pair = cfg.get(cfg.package).value
    content=QCoreApplication.translate("MainWindow", "Delete currently selected translation package. Will be removed: <b>{}</b>").format(cfg.get(cfg.package).value)

    if language_pair == 'None':
        main_window.update_argos_remove_button_state(False)
        main_window.card_deleteargosmodel.setContent(content)
    else:
        from_lang, to_lang = language_pair.split('_')
        package_downloader(main_window, from_lang, to_lang)
        main_window.update_argos_remove_button_state(True)
        main_window.card_deleteargosmodel.setContent(content)
