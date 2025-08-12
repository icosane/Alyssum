from PyQt5.QtCore import QThread, QEventLoop, QTimer, pyqtSignal
from flask import Flask, request, jsonify
import waitress

class TranslateServer(QThread):
    requestTranslation = pyqtSignal(str)

    def __init__(self, main_window, host="127.0.0.1", port=8765, api_key=None, timeout=10):
        super().__init__()
        self.main_window = main_window
        self.host = host
        self.port = port
        self.api_key = api_key
        self.timeout = timeout

        self._app = Flask("AlyssumTranslateServer")

        # --- CORS support ---
        @self._app.after_request
        def add_cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, X-API-Key"
            return response

        @self._app.route("/translate", methods=["POST", "OPTIONS"])
        def translate_route():
            if request.method == "OPTIONS":
                # CORS preflight
                return ("", 200)

            key = request.headers.get("X-API-Key", "")
            if key != self.api_key:
                return jsonify({"error": "unauthorized"}), 401

            data = request.get_json(silent=True) or {}
            text = data.get("text", "").strip()
            if not text:
                return jsonify({"error": "no_text"}), 400

            result = self._translate_sync(text)
            if result is None:
                return jsonify({"error": "timeout"}), 504
            return jsonify({"translated": result})

    def _translate_sync(self, text):
        """Run translation in the main thread and wait until finished or timeout."""
        self.requestTranslation.emit(text)
        loop = QEventLoop()
        result_holder = {"text": None}

        # Backup original handler
        orig_handler = getattr(self.main_window, "on_translation_done", None)

        def handler(translated_text, success):
            result_holder["text"] = translated_text
            loop.quit()

        # Patch temporarily
        setattr(self.main_window, "on_translation_done", handler)

        # Start translation (must happen in main thread)
        #self.main_window.textinputw.setPlainText(text)
        #self.main_window.start_translation_process()

        # Timeout safety
        QTimer.singleShot(int(self.timeout * 1000), loop.quit)

        # Block until done or timeout
        loop.exec_()

        # Restore handler
        if orig_handler:
            setattr(self.main_window, "on_translation_done", orig_handler)

        return result_holder["text"]

    def run(self):
        #print(f"[TranslateServer] Running on http://{self.host}:{self.port}")
        #print(f"[TranslateServer] API Key: {self.api_key}")
        waitress.serve(self._app, host=self.host, port=self.port)

    def stop(self):
        # waitress can't be stopped gracefully from here — you'd have to kill the thread
        self.terminate()

    def get_api_key(self):
        """Return API key for showing in settings."""
        return self.api_key
