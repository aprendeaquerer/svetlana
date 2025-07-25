import tkinter as tk
from tkinter import scrolledtext
from chatgpt_wrapper import ChatGPT

import os
import requests
chatbot = ChatGPT(api_key=os.getenv('CHATGPT_API_KEY'))


# GUI window
window = tk.Tk()
window.title("ChatGPT GUI")
window.geometry("600x600")

# Chat area
chat_area = scrolledtext.ScrolledText(window, wrap=tk.WORD, state='disabled', font=("Segoe UI", 11))
chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Input area
input_frame = tk.Frame(window)
input_frame.pack(padx=10, pady=5, fill=tk.X)

input_box = tk.Entry(input_frame, font=("Segoe UI", 11))
input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))

def send_message():
    user_input = input_box.get()
    if user_input.lower() in {'exit', 'quit'}:
        window.destroy()
        return

    chat_area.config(state='normal')
    chat_area.insert(tk.END, f"You: {user_input}\n")
    chat_area.config(state='disabled')

    input_box.delete(0, tk.END)

    response = chatbot.chat(user_input)

    chat_area.config(state='normal')
    chat_area.insert(tk.END, f"ChatGPT: {response}\n\n")
    chat_area.see(tk.END)
    chat_area.config(state='disabled')

# Send button
send_button = tk.Button(input_frame, text="Send", command=send_message, font=("Segoe UI", 11))
send_button.pack(side=tk.RIGHT)

# Allow pressing Enter to send message
window.bind('<Return>', lambda event: send_message())

def send_saludo_inicial():
    saludo = "saludo inicial"
    chat_area.config(state='normal')
    chat_area.insert(tk.END, f"Tú: {saludo}\n")
    chat_area.config(state='disabled')

    # Llama al backend FastAPI
    try:
        res = requests.post(
            "http://localhost:8000/message",  # Cambia el puerto si es necesario
            json={
                "user_id": "invitado",  # O el user_id que corresponda
                "message": saludo,
                "language": "es"
            }
        )
        data = res.json()
        response = data.get("response", "[Sin respuesta del backend]")
    except Exception as e:
        response = f"[Error al conectar con backend: {e}]"

    chat_area.config(state='normal')
    chat_area.insert(tk.END, f"Eldric: {response}\n\n")
    chat_area.see(tk.END)
    chat_area.config(state='disabled')

# Llama al saludo inicial al abrir la ventana
send_saludo_inicial()

window.mainloop()