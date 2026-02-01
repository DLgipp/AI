import pyttsx3
import time

#engine = pyttsx3.init()

# Выбор голоса (SAPI5)
#voices = engine.getProperty('voices')
#for v in voices:
#    print(v.id, v.name)

VOICE_ID = r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_RU-RU_IRINA_11.0'
RATE = 150
VOLUME = 1.0

def speak(text):
    start_gen = time.time()
    #print("[TTS] START")
    engine = pyttsx3.init()
    
    engine.setProperty('voice', VOICE_ID)
    engine.setProperty('rate', RATE)
    engine.setProperty('volume', VOLUME)
    
    engine.say(text)
    engine.runAndWait()
    engine.stop()
    #print("[TTS] END")
    end_gen = time.time()
    print(f"Текст: {text}")
    print(f"Длительность генерации+воспроизведения: {end_gen - start_gen:.2f} сек")


