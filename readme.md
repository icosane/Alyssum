**Alyssum** is an offline translator that combines the power of [Argos Translate](https://github.com/argosopentech/argos-translate) with [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and [faster-whisper](https://github.com/SYSTRAN/faster-whisper).  
Translate text, documents, books, and even on-screen content — all without an internet connection.  
Privacy-friendly and designed for quick everyday use.

## License

**Alyssum** is licensed under the [GNU Affero General Public License v3.0](./LICENSE).  
You are free to use, modify, and distribute it under the terms of the AGPL-3.0-or-later.

This software also contains third-party components released under various open-source
licenses. Their license texts are provided in the [licenses/](./licenses) directory.

## Features

- Translate text, documents, books, and on-screen content **completely offline**.
- Supports all [languages available](https://github.com/argosopentech/argos-translate?tab=readme-ov-file#supported-languages) in Argos Translate.
- **Integrated OCR** with Tesseract for capturing text from images and PDFs.
- **Voice input** powered by faster-whisper for quick speech-to-translation.
- **Configurable shortcuts** for all main actions — launch OCR, translate, clear windows, copy results, start voice input and translate files.
- **File translation** for `.txt`, `.odt`, `.odp`, `.docx`, `.pptx`, `.epub`, `.html`, `.srt`, and `.pdf`.
- **Browser extension** for translating selectable text without manual copy-paste.
- **GPU acceleration** support for faster translation on compatible NVIDIA cards.

---

## Screenshots

**Main Window**  
![Main Window](./assets/1.png)  

**Settings**  
![Settings](./assets/2.png)  

![](./assets/4.png)  

**OCR in action**  
![OCR in action](./assets/3.gif)

## Download compiled release

Get the latest **Alyssum** release on the [GitHub Releases page](https://github.com/icosane/Alyssum/releases).

> ⚠️ The archive is large and split into **three parts** (`.7z.001`, `.7z.002`, `.7z.003`). Download all parts and extract **only the first part** with [7-Zip](https://www.7-zip.org/) — the rest will combine automatically.

**After extraction:**

* Total size: \~6 GB
* Run `Alyssum.exe`
* Go to **Settings** to download Argos Translate packages for the languages you want.
* If using voice input, download any Whisper model (larger models give better transcription).

## Contents

- [Getting Started](#getting-started)
- [Optional: Building .EXE](#optional-building-exe)
- [Translation Packages](#translation-packages)
- [Tesseract Models](#tesseract-models)
- [Voice input](#voice-input)
- [GPU Acceleration](#gpu-acceleration)
- [Browser Extension](#browser-extension)
- [Registry entries (Windows)](#registry-entries-windows)
- [Acknowledgments, Licenses and Third-Party Software](#acknowledgments-licenses-and-third-party-software)

## Getting Started

>⚠️ If you downloaded the compiled release, skip the installation steps below — just extract the archive and run Alyssum.exe.

### Prerequisites

1. [Python 3.12](https://www.python.org/downloads/release/python-3129/)
2. [Git](https://git-scm.com/downloads)
3. Windows
4. NVIDIA GPU with CUDA 12.6 support *(optional, for GPU acceleration)*

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
   ```bash
   .\Scripts\activate
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
5. Download [Tesseract Portable](https://u.pcloud.link/publink/show?code=XZHY53VZxzxv8qvcTUJ4fzLHJhwvbh7ee1Nk) or [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and place it into:
   ```
   ./AlyssumResources/tesseract
   ```
   Recommended structure:
   ```
   tesseract/
   ├── bin/
   ├── include/
   ├── lib/
   └── share/
       ├── man/
       └── tessdata/
   ```
   If needed, adjust the `TesseractManager` search paths in `config.py`.

   **Tip:** You can also open the folder in [Visual Studio Code](https://code.visualstudio.com/download) or [VSCodium](https://github.com/VSCodium/vscodium/releases), install the Python extension, then press `Ctrl+Shift+P` → **Python: Create Environment** → `.venv` → select `requirements.txt`.

6. Enable UTF-8 support in Windows *(recommended for files with non-Latin characters)*:  
   - **Settings** → **Time & language** → **Language & region** → **Administrative language settings** → **Change system locale**  
   - Check **Beta: Use Unicode UTF-8 for worldwide language support**  
   - Reboot for changes to apply.

---

## Optional: Building .EXE

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Run:
   ```bash
   pyinstaller build.spec
   ```

*(The `build.spec` file is included in the repository.)*

---

## Translation Packages

Download Argos Translate packages via the Settings page, or manually from [here](https://www.argosopentech.com/argospm/index/).

For manual install extract the folder into:
```
AlyssumResources/models/argostranslate/data/argos-translate/packages
```

Example structure:
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
Folder naming: `langfrom_langto` or `translate-langfrom_langto-version`.

---

## Tesseract Models

Get models from:
- [tessdata_fast (faster, slightly less accurate)](https://github.com/tesseract-ocr/tessdata_fast)
- [tessdata (more accurate, slower)](https://github.com/tesseract-ocr/tessdata)

Place them into:
```
AlyssumResources/tesseract/share/tessdata
```

---

## Voice input

Select your preferred Whisper model in **Settings** — options include `tiny`, `base`, `small`, `medium`, `large-v1`, `large-v2`, `large-v3`, `large`, and `large-v3-turbo`. 

`.en` models are hidden (English-only), and distil models are excluded due to performance issues during testing.

Downloaded models are stored in: `AlyssumResources/models/whisper`.

---

## GPU Acceleration

If CUDA is available, the app will automatically detect and use it for faster translation.

---

## Browser Extension

### Chrome
1. Enable **Developer mode** in `chrome://extensions/`.
2. Click **Load unpacked** and select the `alyssum-ext` folder.

> ⚠️ If you try to install the `.crx` directly, Chrome may block it because it is not from the Chrome Web Store. Use **Load unpacked** instead.

*(Optional: For Ungoogled Chromium or Supermium, you can enable `chrome://flags/#extension-mime-request-handling` → **Always prompt for install**, then drag the `.crx` file into Chrome.)*

### Firefox
1. Open `about:config`.
2. Set `xpinstall.signatures.required` to `false`.
3. Open **Add-ons Manager** → **Settings** → **Install Add-on From File**.
4. Select `firefox.xpi`.

After installation, go to the app settings, copy the API key, and paste it into the extension settings.
> **Note:** The API key only needs to be set once.

> ⚠️ **Important:** If using uBlock Origin, make sure to **disable the `Block Outsider Intrusion into LAN` filter**. Otherwise, extension will not be able to communicate with the local server.
---

## Registry entries (Windows)
The application saves the window size, position, and API key in the system registry. To clear these settings, simply delete the following registry key:
```
HKEY_CURRENT_USER\Software\icosane\Alyssum
```
---

## Acknowledgments, Licenses and Third-Party Software

This project uses the following libraries and components, which may be licensed under open-source or proprietary terms.  
Full license texts for each component are included in the [licenses/](./licenses) directory.

### Core Libraries
- [Argos Translate](https://github.com/argosopentech/argos-translate) - Machine translation library, licensed under the [MIT License](./licenses/argos-translate-LICENSE.txt)
- [Tesseract OCR Engine](https://github.com/tesseract-ocr/tesseract) - an OCR engine, licensed under the [Apache License 2.0](./licenses/tesseract-LICENSE.txt)
- [QFluentWidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - a fluent design widgets library, licensed under the [GNU General Public License v3.0](./licenses/PyQt-Fluent-Widgets-LICENSE.txt) 
- [argos-translate-files](https://github.com/LibreTranslate/argos-translate-files) - File translation via Argos Translate, licensed under the [GNU Affero General Public License v3.0](./licenses/argos-translate-files-LICENSE.txt) 
- [PyQt5](https://pypi.org/project/PyQt5/) - Python bindings for Qt v5, licensed under the [GNU General Public License v3.0](./licenses/PyQt-LICENSE.txt) 
- [Flask](https://pypi.org/project/Flask/) - Micro web framework,  licensed under the [BSD 3-Clause License](./licenses/flask-LICENSE.txt) 
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper/) - audio to text transcription, licensed under the [MIT License](./licenses/faster-whisper-LICENSE.txt)

### Supporting Libraries & Tools
- [langdetect](https://github.com/Mimino666/langdetect) - Language detection, licensed under the [Apache License 2.0](./licenses/langdetect-LICENSE.txt)
- [pytesseract](https://github.com/madmaze/pytesseract) - a Python wrapper for Google Tesseract, licensed under the [Apache License 2.0](./licenses/pytesseract-LICENSE.txt) 
- [opencv-python](https://github.com/opencv/opencv-python) - a library for computer vision and image processing, licensed under the [MIT License](./licenses/opencv-python-LICENSE.txt)
- [pyautogui](https://github.com/asweigart/pyautogui) - GUI automation, licensed under the [BSD 3-Clause License](./licenses/pyautogui-LICENSE.txt)
- [pillow](https://github.com/python-pillow/Pillow) - Python Imaging Library, licensed under the [MIT-CMU License](./licenses/pillow-LICENSE.txt) 
- [nvidia-cuda-runtime](https://pypi.org/project/nvidia-cuda-runtime-cu12/) - GPU runtime, licensed under the [NVIDIA EULA](./licenses/nvidia-EULA.pdf) 
- [nvidia-cudnn](https://pypi.org/project/nvidia-cudnn-cu12/) - Deep learning acceleration, licensed under the [NVIDIA EULA](./licenses/nvidia-EULA.pdf) 
- [nvidia-cublas](https://pypi.org/project/nvidia-cublas-cu12/) - GPU BLAS library, licensed under the [NVIDIA EULA](./licenses/nvidia-EULA.pdf) 
- [PyInstaller](https://pyinstaller.org/) - bundles a Python application and all its dependencies into a single package. Licensed under the [GPL 2.0 License and the Apache License 2.0](./licenses/pyinstaller-COPYING.txt) 
- [waitress](https://pypi.org/project/waitress/) - WSGI server, licensed under the [Zope Public License (ZPL) 2.1](./licenses/waitress-LICENSE.txt)   
- [jsonify](https://pypi.org/project/jsonify/) - CSV-to-JSON converter, licensed under the [MIT License](./licenses/jsonify-LICENSE.txt)
- [pytorch](https://github.com/pytorch/pytorch) - Deep learning framework, licensed under the [pytorch License](./licenses/pytorch-LICENSE.txt)
- [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/) - audio I/O library, licensed under the [MIT License](./licenses/pyaudio-LICENSE.txt)
- [psutil](https://github.com/giampaolo/psutil) - process and system monitoring, licensed under the [BSD 3-Clause License](./licenses/psutil-LICENSE.txt)

### Resources & References
- [Tesseract portable](https://forum.powerbasic.com/forum/user-to-user-discussions/powerbasic-for-windows/826079-portable-tesseract)
- [Letter T icons](https://www.flaticon.com/free-icons/letter-t) by Luch Phou – Flaticon
- [Sl-Alex for ShortcutEdit](https://sl-alex.net/gui/2022/08/21/shortcutedit_capturing_shortcuts_in_pyqt/)

**This software contains source code provided by NVIDIA Corporation.**

> **NOTE**: This software depends on packages that may be licensed under different open-source or proprietary licenses.
---
