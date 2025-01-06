# Q&A Chatbot

## Project Overview
This project is focused on creating a Q&A chatbot using LangChain. The chatbot is powered by the LLM Llama 3.2, which enables it to process and generate answers to user queries effectively.

## Features
- **Q&A Functionality**: The chatbot is designed to answer questions based on the input provided by the user.
- **Powered by Llama 3.2**: The Llama 3.2 model is integrated into the system to handle natural language understanding and generation, ensuring accurate and context-aware responses.
- **LangChain Integration**: LangChain is used to enhance the chatbot’s capabilities by allowing it to retrieve, process, and respond to queries in an efficient and scalable manner.

## Technology Stack
- **Llama 3.2**: A large language model used to generate responses.
- **LangChain**: A framework for building language model-based applications.

## How it Works
The chatbot operates by taking user input in the form of questions. It processes these queries through Llama 3.2, which uses advanced NLP techniques to understand the context and generate relevant answers. LangChain is used to facilitate the integration and orchestration of various components that support the chatbot's functioning.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/ShubhamSinghCMR/Generative-AI.git
  ```
2. Install the required dependencies:
  ```
  pip install -r requirements.txt
  ```
3. Running the Application:
  ```
  streamlit run chatbot.py    
  ```