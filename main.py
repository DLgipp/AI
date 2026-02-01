from modules.core.dialog_core import DialogueCore

from modules.stt.runner import run_stt_loop
from modules.llm.ollama_client import generate_response
from modules.tts.tts import speak


def main():
    dialog = DialogueCore(history_size=10)

    while True:

        
        if dialog.is_speaking():
            continue

        user_text = run_stt_loop()
        if not user_text:
            continue

        dialog.push_user_message(user_text)

        msg = dialog.pop_next()
        if msg["role"] != "user":
            continue

        response = generate_response(msg["text"], dialog.get_history())
        dialog.push_assistant_message(response)

        assistant_msg = dialog.pop_next()
        if assistant_msg and dialog.can_speak():
            dialog.set_speaking()

            print("AI:", assistant_msg["text"])
            speak(assistant_msg["text"])  # ⬅ блокирующий вызов

            dialog.set_listening()



if __name__ == "__main__":
    main()
