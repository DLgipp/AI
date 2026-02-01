from faster_whisper import WhisperModel
from config import WHISPER_MODEL, WHISPER_LANGUAGE


class WhisperSTT:
    def __init__(self):
        self.model = WhisperModel(
            WHISPER_MODEL,
            device="cuda",
            compute_type="float16"
        )

    def transcribe(self, audio):
        segments, _ = self.model.transcribe(
            audio,
            language=WHISPER_LANGUAGE,
            beam_size=5
        )

        text = []
        for segment in segments:
            text.append(segment.text)

        return " ".join(text).strip()
