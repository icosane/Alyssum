from enum import Enum
import os, sys
from pathlib import Path
import pytesseract
from PyQt5.QtCore import QLocale
from PyQt5.QtGui import QKeySequence
from qfluentwidgets import (qconfig, QConfig, OptionsConfigItem, Theme,
                            OptionsValidator, EnumSerializer, ConfigSerializer, ConfigItem, BoolValidator)


class ArgosPathManager:
    """Manages Argos Translate directory configuration"""

    @staticmethod
    def initialize():
        """Set up custom directories for Argos Translate"""
        # Set base directory
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)  # PyInstaller bundle
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        ARGOS_PACKAGES_DIR = os.path.join(base_dir, "AlyssumResources", "models", "argostranslate")
        os.makedirs(ARGOS_PACKAGES_DIR, exist_ok=True)

        # Set environment variables
        os.environ.update({
            "XDG_DATA_HOME": str(Path(ARGOS_PACKAGES_DIR) / "data"),
            "XDG_CONFIG_HOME": str(Path(ARGOS_PACKAGES_DIR) / "config"),
            "XDG_CACHE_HOME": str(Path(ARGOS_PACKAGES_DIR) / "cache"),
            "ARGOS_PACKAGES_DIR": str(Path(ARGOS_PACKAGES_DIR) / "data" / "argos-translate" / "packages"),
            "ARGOS_TRANSLATE_DATA_DIR": str(Path(ARGOS_PACKAGES_DIR) / "data"),
            "ARGOS_DEVICE_TYPE": "cpu"
        })

        # Create directories
        Path(os.environ["ARGOS_PACKAGES_DIR"]).mkdir(parents=True, exist_ok=True)

        return ARGOS_PACKAGES_DIR

class TesseractManager:
    @staticmethod
    def initialize():
        """Set up custom directories for Tesseract"""
        # Set base directory
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)  # PyInstaller bundle
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        TESSDATA_PREFIX = os.path.join(base_dir, "AlyssumResources", "tesseract", "share", "tessdata")
        pytesseract.pytesseract.tesseract_cmd = os.path.join(base_dir, "AlyssumResources", "tesseract", "bin", "tesseract.exe")

        # Set environment variables
        os.environ.update({
            "TESSDATA_PREFIX": str(Path(TESSDATA_PREFIX)),
        })

        return TESSDATA_PREFIX


# Initialize Argos paths BEFORE any Argos Translate imports
ArgosPathManager.initialize()

from argostranslate import argospm

TesseractManager.initialize()

class Language(Enum):
    """ Language enumeration """

    ENGLISH = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)
    RUSSIAN = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)
    AUTO = QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)

class LanguageSerializer(ConfigSerializer):
    """ Language serializer """

    def serialize(self, language):
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


available_packages = argospm.get_available_packages()

TranslationPackage = Enum(
    'TranslationPackage',
    {
        **{"NONE": "None"},
        **{f"{pkg.from_code.upper()}_TO_{pkg.to_code.upper()}": f"{pkg.from_code}_{pkg.to_code}"
           for pkg in available_packages}
    }
)

class TranslationPackageSerializer(ConfigSerializer):
    """ Translation package serializer """

    def __init__(self):
        self.package_map = {package.value: package for package in TranslationPackage}

    def serialize(self, package):
        return package.value if package != TranslationPackage.NONE else "None"

    def deserialize(self, value: str):
        if value == "None":
            return TranslationPackage.NONE
        package = self.package_map.get(value)
        if package is None:
            raise ValueError(f"Invalid translation package: {value}")
        return package

class KeyCombinationSerializer(ConfigSerializer):
    def serialize(self, value: QKeySequence) -> object:
        return value[0] if not value.isEmpty() else 0

    def deserialize(self, value: object) -> QKeySequence:
        if isinstance(value, int):
            return QKeySequence(value)
        elif isinstance(value, str):
            return QKeySequence(value)
        else:
            return QKeySequence()



class KeyCombinationConfigItem(ConfigItem):
    def __init__(self, group: str, key: str, default: str):
        super().__init__(group, key, QKeySequence(default), serializer=KeyCombinationSerializer())

class Config(QConfig):
    language = OptionsConfigItem(
        "Settings", "language", QLocale.Language.English, OptionsValidator(Language), LanguageSerializer(), restart=True)
    themeMode = OptionsConfigItem("Window", "themeMode", Theme.AUTO,
                                OptionsValidator(Theme), EnumSerializer(Theme), restart=True)
    dpiScale = OptionsConfigItem(
        "Settings", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    package = OptionsConfigItem(
        "Translation", "package", TranslationPackage.NONE, OptionsValidator(TranslationPackage), TranslationPackageSerializer(), restart=False)
    shortcuts = ConfigItem("Shortcuts", "shortcuts", False, BoolValidator())
    ocrcut = KeyCombinationConfigItem("Shortcuts", "OCR", "F1")
    tlcut = KeyCombinationConfigItem("Shortcuts", "Translation", "F2")
    clcut = KeyCombinationConfigItem("Shortcuts", "Clear windows", "F3")
    copycut = KeyCombinationConfigItem("Shortcuts", "SelectAndCopy", "F5")
    filecut = KeyCombinationConfigItem("Shortcuts", "FileTranslation", "F6")


cfg = Config()
qconfig.load('config/config.json', cfg)
