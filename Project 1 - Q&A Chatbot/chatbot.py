from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import OllamaLLM as Ollama

import streamlit as st

# Frontend
st.title("Q&A Chatbot using Ollama")
input_text = st.text_input("Search the topic you want")

# Prompt for LLM
prompt = ChatPromptTemplate.from_messages([
    ("system", "Please respond to user query"),
    ("user", "{question}")
])

# LLM Model
llm = Ollama(model="llama3.2")

# Chain
output = StrOutputParser()
chain = prompt | llm | output

if input_text:
    st.write(chain.invoke({"question":input_text}))
