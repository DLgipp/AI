import torch
import sounddevice as sd
import numpy as np
import soundfile as sf
from qwen_tts import Qwen3TTSModel
import re

model = Qwen3TTSModel.from_pretrained(
    "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
    device_map="cuda:0",
    dtype=torch.bfloat16,
    #attn_implementation="flash_attention_2",
)

ref_audio = "./modules/tts/origin1.wav"
ref_text  = "Да пофиг, что он - красавчик! Я таких не перевариваю. Видно же что я фанатка, рас повесила брелок на сумку! По вашему нормально вот так смеятся над чужими увлечениями? "


text="Ха-ха! Привет тебе тоже! Нам нужно было начать сначала, кажется? Хорошо, давай начнем заново! Как тебя зовут, и что ты хочешь обсудить или рассказать? Ммм... я чувствую, что у нас впереди много интересного!"

sentences = re.split(r'(?<=[.!?])\s+', text)
wavs, sr = model.generate_voice_clone(
        text=text,
        language="Russian",
        ref_audio=ref_audio,
        ref_text=ref_text,
    )
sf.write("output_voice_clone1.wav", wavs[0], sr)
sd.play(np.array(wavs[0]), samplerate=sr)
sd.wait() 
"""for sentence in sentences:
    wavs, sr = model.generate_voice_clone(
        text=sentence,
        language="Russian",
        ref_audio=ref_audio,
        ref_text=ref_text,
    )
    audio_array = np.array(wavs[0])
    
    sd.wait()"""