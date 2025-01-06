import streamlit as st
import requests

st.title("Client End of ChatBot")
input_text = st.text_input("Enter your query")

def call_llm_api(input_text: str):
    payload = {
        "input": {  # Wrap the question in an input key
            "question": input_text
        }
    }
    response = requests.post("http://127.0.0.1:8000/ask/invoke", json = payload)
    return response.json()['output']

if input_text:
    st.write(call_llm_api(input_text))
