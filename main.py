import time

from modules.core.dialog_core import DialogueCore
from modules.llm.ollama_client import generate_response
from modules.tts.tts import speak

from modules.events.event_bus import EventBus
from modules.events.policy import ReactivePolicy
from modules.stt.controller import STTController


def main():
    # =========================
    # ИНФРАСТРУКТУРА
    # =========================
    bus = EventBus()

    dialog = DialogueCore(history_size=10)
    policy = ReactivePolicy(dialog)

    stt = STTController(bus)

    # =========================
    # EVENT HANDLERS
    # =========================
    def on_user_text(event):
        text = event.payload["text"]

        dialog.push_user_message(text)

        msg = dialog.pop_next()
        if msg and msg["role"] == "user":
            response = generate_response(
                msg["text"],
                dialog.get_history()
            )
            dialog.push_assistant_message(response)

    bus.subscribe("user_text", on_user_text)
    bus.subscribe("silence_timeout", policy.handle_event)

    # =========================
    # MAIN LOOP
    # =========================
    while True:
        # STT работает всегда
        stt.tick()

        # Ассистент говорит, если может
        assistant_msg = dialog.pop_next()
        if assistant_msg and assistant_msg["role"] == "assistant" and dialog.can_speak():
            dialog.set_speaking()
            speak(assistant_msg["text"])  # блокирующий TTS
            dialog.set_listening()

        time.sleep(0.02)


if __name__ == "__main__":
    main()
