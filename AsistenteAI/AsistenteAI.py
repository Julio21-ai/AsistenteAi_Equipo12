# -*- coding: latin-1 -*-
import base64
import subprocess
import sys
import tkinter as tk
from tkinter import scrolledtext, messagebox
import os
from typing import List, Dict
from datetime import datetime
from litellm import completion

# === CONFIGURACIÓN API_KEY ===
def load_api_key(file_path="apikey.key") -> str:
    """Carga la API key desde un archivo codificado o desde variable de entorno."""
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                encoded_key = f.read().strip()
                decoded_key = base64.b64decode(encoded_key).decode("utf-8")
                return decoded_key
        except Exception as e:
            raise ValueError(f"Error al leer o decodificar la API key: {e}")
    elif "API_KEY" in os.environ:
        return os.environ["API_KEY"]
    else:
        raise ValueError("No se encontró la API key ni en archivo ni en variable de entorno.")

API_KEY = load_api_key()

if API_KEY is None:
    raise ValueError("No se encontró la API_KEY en las variables de entorno.")

response_cache = {}

# === LÓGICA DE RESPUESTA ===
def generate_response(messages: List[Dict]) -> str:
    cache_key = tuple(tuple(d.items()) for d in messages)
    if cache_key in response_cache:
        return response_cache[cache_key]
    try:
        response = completion(
            model="openai/gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            api_key=API_KEY
        )
        content = response['choices'][0]['message']['content']
        response_cache[cache_key] = content
        return content
    except Exception as e:
        return f"Error al generar respuesta: {e}"

# === INTERFAZ DE USUARIO ===
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Asistente de Estudio")

        self.messages = [
          {"role": "system",
           "content":(
            "You are an academic assistant who helps students with study-related questions. "
            "You must not respond to any message that contains offensive, vulgar, violent, or inappropriate language. "
            "If the user asks something offensive or inappropriate, politely respond that you cannot help with that request.")
           }
         ]

        self.chat_box = scrolledtext.ScrolledText(
          root, wrap=tk.WORD, width=80, height=20, state="disabled", font=("Calibri", 12))

        self.chat_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.entry = tk.Entry(root, width=80)
        self.entry.pack(fill=tk.X, padx=10, pady=5)

        self.entry.bind("<Return>", self.send_message)
        self.root.bind("<Return>", self.send_message)
        self.entry.focus_set()

        self.send_button = tk.Button(
          root, text="Enviar", command=self.send_message)
        self.send_button.pack(pady=5)

        self.view_button = tk.Button(
          root, text="Ver conversación", command=self.open_conversation_file)
        self.view_button.pack(pady=5)

        self.history_file = "conversacion.txt"

    def send_message(self, event=None):
        user_input = self.entry.get().strip()
        if not user_input:
            return

        self.append_chat("Tú", user_input)
        self.messages.append({"role": "user", "content": user_input})
        self.entry.delete(0, tk.END)

        response = generate_response(self.messages)
        self.append_chat("Asistente", response)
        self.messages.append({"role": "assistant", "content": response})

        self.save_to_file("Tú", user_input)
        self.save_to_file("Asistente", response)

    def append_chat(self, sender, message):
        self.chat_box.config(state="normal")
        self.chat_box.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_box.yview(tk.END)
        self.chat_box.config(state="disabled")

    def save_to_file(self, sender, message):
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(self.history_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] {sender}: {message}\n\n")
            except Exception as e:
                messagebox.showerror("Error",
                    f"No se pudo guardar la conversación: {e}")


    def open_conversation_file(self):
        try:
            if os.path.exists(self.history_file):
                if sys.platform.startswith("win"):
                    os.startfile(self.history_file)

                elif sys.platform.startswith("darwin"):
                    subprocess.call(("open", self.history_file))

                else:
                    subprocess.call(("xdg-open", self.history_file))
            else:
                messagebox.showinfo("Información", "No hay conversación guardada todavía.")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

# === EJECUCIÓN DE LA APP ===
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

