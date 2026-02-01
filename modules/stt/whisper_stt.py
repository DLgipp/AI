from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_LANGUAGE
from modules.stt.logger import log

class WhisperSTT:
    def __init__(self):
        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cuda",
            compute_type="float16"
        )
        log("Whisper model initialized", role="SYSTEM", stage="WhisperSTT")

    def transcribe(self, audio):
        log("Transcription started", role="PIPELINE", stage="WhisperSTT", payload=f"{len(audio)} samples")
        segments, _ = self.model.transcribe(
            audio,
            language=WHISPER_LANGUAGE,
            beam_size=5
        )

        text = []
        for segment in segments:
            text.append(segment.text)
        log("Transcription finished", role="PIPELINE", stage="WhisperSTT", payload=f"{len(text)} chars")
        return " ".join(text).strip()
