from chatgpt_wrapper import ChatGPT

import os
chatbot = ChatGPT(api_key=os.getenv('CHATGPT_API_KEY'))


chatbot = ChatGPT(api_key=API_KEY)

print("Start chatting with ChatGPT (type 'exit' to stop):\n")

while True:
    prompt = input("You: ")
    if prompt.lower() in {'exit', 'quit'}:
        print("Exiting chat. Goodbye!")
        break
    response = chatbot.chat(prompt)
    print(f"ChatGPT: {response}\n")