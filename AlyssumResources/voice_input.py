import os, wave, tempfile
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QMutex
import pyaudio
import psutil
from faster_whisper import WhisperModel


class ModelLoader(QThread):
    model_loaded = pyqtSignal(object)

    def __init__(self, model_name, device):
        super().__init__()
        self.model_name = model_name
        self.device = device

    def run(self):
        model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type="float32" if self.device == "cpu" else "float16",
            cpu_threads=psutil.cpu_count(logical=False),
            download_root="./AlyssumResources/models/whisper",
            local_files_only=True
        )
        self.model_loaded.emit(model)


class AudioStreamHandler(QObject):
    recording_finished = pyqtSignal(str)  # emits path to temp file

    def __init__(self):
        super().__init__()
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recording = False
        self.audio_buffer = []
        self.stream_lock = QMutex()

    def start_recording(self):
        self.stream = self.p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=1024
        )
        self.recording = True
        self.audio_buffer = []

    def stop_recording(self):
        self.recording = False
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        # save to temp file
        fd, path = tempfile.mkstemp(suffix=".wav", dir=tempfile.gettempdir())
        os.close(fd)
        wf = wave.open(path, "wb")
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(16000)
        wf.writeframes(b"".join(self.audio_buffer))
        wf.close()

        self.recording_finished.emit(path)

    def read_audio_data(self):
        if self.stream is None:
            return None
        try:
            self.stream_lock.lock()
            data = self.stream.read(1024, exception_on_overflow=False)
        finally:
            self.stream_lock.unlock()
        return data


class AudioThread(QThread):
    def __init__(self, handler: AudioStreamHandler):
        super().__init__()
        self.handler = handler
        self.running = True

    def run(self):
        while self.running:
            if self.handler.recording:
                data = self.handler.read_audio_data()
                if data:
                    self.handler.audio_buffer.append(data)
            self.msleep(30)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class TranscriptionWorker(QThread):
    transcription_done = pyqtSignal(str)

    def __init__(self, model, audio_file):
        super().__init__()
        self.model = model
        self.audio_file = audio_file

    def run(self):
        try:
            segments, _ = self.model.transcribe(self.audio_file)
            text = "".join([seg.text for seg in segments])
            self.transcription_done.emit(text.strip())
        finally:
            try:
                if os.path.exists(self.audio_file):
                    os.remove(self.audio_file)
            except Exception:
                pass


class VoiceController(QObject):
    """ High-level manager for recording + transcription. """
    transcription_ready = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    def __init__(self, whisper_model_name, device):
        super().__init__()
        self.model_name = whisper_model_name
        self.device = device
        self.model = None

        self.audio_handler = AudioStreamHandler()
        self.audio_thread = AudioThread(self.audio_handler)
        self.audio_thread.start()

        self.audio_handler.recording_finished.connect(self._on_recording_finished)

    def load_model(self):
        """Load Whisper model in a thread."""
        self.loader = ModelLoader(self.model_name, self.device)
        self.loader.model_loaded.connect(self._on_model_loaded)
        self.loader.start()

    def _on_model_loaded(self, model):
        self.model = model

    def toggle_recording(self):
        if not self.model:
            # load model lazily
            self.recording_started.emit()  # placeholder can show "Loading..."
            self.loader = ModelLoader(self.model_name, self.device)
            self.loader.model_loaded.connect(self._on_model_loaded_and_record)
            self.loader.start()
            return

        if not self.audio_handler.recording:
            self.audio_handler.start_recording()
            self.recording_started.emit()
        else:
            self.audio_handler.stop_recording()
            self.recording_stopped.emit()

    def _on_model_loaded_and_record(self, model):
        self.model = model
        # start recording immediately once model is ready
        self.audio_handler.start_recording()
        self.recording_started.emit()


    def _on_recording_finished(self, filepath):
        self.worker = TranscriptionWorker(self.model, filepath)
        self.worker.transcription_done.connect(self.transcription_ready.emit)
        self.worker.start()

    def stop(self):
        self.audio_thread.stop()
