from dotenv import load_dotenv
from agents.chat_agent import ChatAgent
from utils.reader import read_file_text

import gradio

load_dotenv()

name = read_file_text("../data/name.txt")
summary = read_file_text("../data/profile.md")

agent = ChatAgent(name, summary, {})

chat_interface = gradio.ChatInterface(agent.chat, type = "messages")
chat_interface.launch()