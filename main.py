import asyncio

from modules.core.dialog_core import DialogueCore
from modules.llm.ollama_client import generate_response_async  # async версия
from modules.tts.tts import speak_async  # async версия
from modules.events.event_bus import EventBus
from modules.events.policy import ReactivePolicy
from modules.stt.controller import STTController


async def stt_loop(stt: STTController):
    loop = asyncio.get_event_loop()
    """Постоянный цикл STT."""
    while True:
        await loop.run_in_executor(None, stt.tick)
        await asyncio.sleep(0.02)


async def tts_loop(dialog: DialogueCore):
    """Цикл, отвечающий за произнесение ассистента."""
    while True:
        assistant_msg = dialog.pop_next()
        if assistant_msg and assistant_msg["role"] == "assistant" and dialog.can_speak():
            dialog.set_speaking()
            await speak_async(assistant_msg["text"])  # async TTS
            dialog.set_listening()
        await asyncio.sleep(0.02)


async def llm_handler(event, dialog: DialogueCore):
    """Обработка нового пользовательского текста."""
    text = event.payload["text"]
    dialog.push_user_message(text)

    msg = dialog.pop_next()
    if msg and msg["role"] == "user":
        # Асинхронная генерация ответа
        response = await generate_response_async(msg["text"], dialog.get_history())
        dialog.push_assistant_message(response)


async def main():
    # =========================
    # ИНФРАСТРУКТУРА
    # =========================
    loop = asyncio.get_running_loop()  # главный loop
    bus = EventBus(loop)
    dialog = DialogueCore(history_size=10)
    policy = ReactivePolicy(dialog)
    stt = STTController(bus)
    
    # =========================
    # EVENT HANDLERS
    # =========================
    def handler(e):
        #asyncio.create_task(llm_handler(e, dialog))
        return llm_handler(e, dialog)

    bus.subscribe("user_text", handler)
    #bus.subscribe("user_text", lambda e: asyncio.create_task(llm_handler(e, dialog)))
    bus.subscribe("silence_timeout", policy.handle_event)

    # =========================
    # ЗАПУСК ПАРАЛЛЕЛЬНЫХ ЦИКЛОВ
    # =========================
    await asyncio.gather(
        stt_loop(stt),
        tts_loop(dialog),
    )


if __name__ == "__main__":
    asyncio.run(main())
