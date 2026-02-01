from config import MAX_HISTORY

history = []

def get_history():
    return history[-1*MAX_HISTORY:]

def add_to_history(user_input, model_response):
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": model_response})
    if len(history) >  MAX_HISTORY:
        #history[:] = history[-2*MAX_HISTORY:]
        history.pop(0)
