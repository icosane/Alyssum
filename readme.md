A simple translator built on Argos Translate and Tesseract.

## Features

- **Languages**: Support is available for most Argos Translate packages, although new packages will need to be manually added to the list.
- **OCR support**: Integrated Google Tesseract engine
- **Configurable shortcuts**: By default, you can use the following keys for various functions: **F1** to launch OCR, **F2** to translate, **F3** to clear windows, **F5** to copy the translation to the clipboard, and **F6** to translate files. All of these shortcuts can be remapped in the settings. (Note that shortcuts are disabled by default; you can enable them in the settings.)
- **File Translation**: You can translate the following file formats: **.txt**, **.odt**, **.odp**, **.docx**, **.pptx**, **.epub**, **.html**, **.srt**, and **.pdf**.

## Getting Started

### Prerequisites

1) [Python 3.12](https://www.python.org/downloads/release/python-3129/)
2) [Git](https://git-scm.com/downloads)
3) Windows

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/icosane/Alyssum.git
   ```

2. Navigate to the folder and create a virtual environment:
    ```bash
    python -m venv .
    ```
3. Activate the virtual environment:
    ```
    .\\Scripts\\activate
    ```
4. Install the requirements from the file: 
    ```
    pip install -r requirements.txt
    ```

5. Download [Tesseract Portable](https://u.pcloud.link/publink/show?code=XZHY53VZxzxv8qvcTUJ4fzLHJhwvbh7ee1Nk) or [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and place it into ```./AlyssumResources/tesseract```   
I prefer the first option, which has the following file structure:
    ```
    tesseract/
    ├── bin/
    ├── include/
    ├── lib/
    └── share/
        ├── man/
        └── tessdata/
    ```
    You may need to modify the ```TesseractManager``` class in ```config.py``` to update the directories it searches.

You can also open the extracted folder in [Visual Studio Code](https://code.visualstudio.com/download) / [VSCodium](https://github.com/VSCodium/vscodium/releases), install Python extension, then press ```Ctrl+Shift+P```, type ```Python: Create Environment```, select ```.venv```, use ```requirements.txt``` and wait for the process to complete.

6. Enable UTF-8 support in Windows (for translating files with non-Latin characters): 

    Go to Windows Settings > Time & language > Language & region > Administrative language settings > Change system locale, and check Beta: Use Unicode UTF-8 for worldwide language support. Then reboot the PC for the change to take effect.

## Building .EXE
1. Install PyInstaller in your .venv:
```pip install pyinstaller```
2. Run ```pyinstaller build.spec```

## Translation packages
You can download Argos Translate packages from the package selection menu located on the Settings page. Alternatively, you can download them [here](https://www.argosopentech.com/argospm/index/), extract the folder, and place them into

>AlyssumResources\models\argostranslate\data\argos-translate\packages
```
AlyssumResources
└── models
    └── argostranslate
        └── data
            └── argos-translate
                └── packages
                    ├── translate-en_fr-1.9
                    │   ├── model
                    │   ├── stanza
                    │   ├── metadata.json         
                    │   ├── README.md                 
                    │   └── config.json
                    └── en_de
                        ├── model
                        ├── stanza
                        ├── metadata.json  
                        ├── README.md 
                        └── config.json
```
The folders can be named using either the format **langfrom_langto** or **translate-langfrom_langto-version**.

## Tesseract models
You can obtain Tesseract models from either [this link](https://github.com/tesseract-ocr/tessdata_fast) or [this link](https://github.com/tesseract-ocr/tessdata). After downloading, place them in  **AlyssumResources\tesseract\share\tessdata**.

## Acknowledgments
- [QFluentWidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [Argos Translate](https://github.com/argosopentech/argos-translate)
- [Tesseract OCR Engine](https://github.com/tesseract-ocr/tesseract)
- [PyQt5](https://pypi.org/project/PyQt5/)
- [langdetect](https://github.com/Mimino666/langdetect)
- [pytesseract](https://github.com/madmaze/pytesseract)
- [opencv-python](https://github.com/opencv/opencv-python)
- [pyautogui](https://github.com/asweigart/pyautogui)
- [pillow](https://github.com/python-pillow/Pillow)
- [PyInstaller](https://pyinstaller.org/)
- [Tesseract portable](https://forum.powerbasic.com/forum/user-to-user-discussions/powerbasic-for-windows/826079-portable-tesseract)
- [Letter t icons](https://www.flaticon.com/free-icons/letter-t) - Letter t icons created by Luch Phou - Flaticon
- [Sl-Alex for ShortcutEdit](https://sl-alex.net/gui/2022/08/21/shortcutedit_capturing_shortcuts_in_pyqt/)
- [argos-translate-files](https://github.com/LibreTranslate/argos-translate-files)
- [JSchmie for PDF support in argos-translate-files](https://github.com/LibreTranslate/argos-translate-files/pull/13)

## Screenshots
<div style="display: flex; flex-direction: column;">
    <p><center>Main Window</center></p>
    <img src="./assets/1.png" alt="ui" style="margin-right: 10px;" />
    <p><center>Settings</center></p>
    <img src="./assets/2.png" alt="ui" style="margin-right: 10px;"/>
    <p><center>OCR in action</center></p>
    <img src="./assets/3.gif" alt="ui" style="margin-right: 10px;"/>
</div>

