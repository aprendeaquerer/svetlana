# chatgpt_wrapper.py
from openai import OpenAI

class ChatGPT:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        self.messages = []

    def chat(self, message):
        self.messages.append({"role": "user", "content": message})
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=self.messages
        )
        reply = response.choices[0].message.content
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        self.messages.clear()
