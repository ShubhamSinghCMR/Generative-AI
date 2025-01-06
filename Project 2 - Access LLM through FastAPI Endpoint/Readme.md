# Q&A Chatbot

## Project Overview
This project is focused on creating a Q&A chatbot using LangChain, with the frontend and backend separated. The backend is powered by FastAPI and communicates with the LLM Llama 3.2 to generate answers to user queries. The frontend, developed using Streamlit, makes requests to the backend API to retrieve the answers.

## Features
- **Q&A Functionality**: The chatbot allows users to input questions, and it responds with relevant answers.
- **Powered by Llama 3.2**: The Llama 3.2 model is integrated to generate responses based on user queries.
- **FastAPI Backend**: The backend is built with FastAPI, serving API endpoints that the frontend can query to get answers.
- **Streamlit Frontend**: The frontend is a simple user interface built with Streamlit that communicates with the backend API.

## Technology Stack
- **Llama 3.2**: A large language model used to generate responses.
- **LangChain**: A framework for building language model-based applications.
- **FastAPI**: A modern web framework for building APIs with Python.
- **Streamlit**: A framework for building interactive user interfaces for machine learning applications.

## How it Works
The backend (FastAPI) handles user queries by processing them through Llama 3.2 to generate relevant answers. The frontend, built with Streamlit, sends HTTP requests to the FastAPI backend to retrieve the answers. The two components work together seamlessly to provide the user with a Q&A chatbot experience.

## Installation

1. Clone this repository: git clone https://github.com/ShubhamSinghCMR/Generative-AI.git
2. Install the required dependencies using requirements.txt file from source folder: pip install -r requirements.txt
3. To run the backend server, use the following command: python app.py
4. To run the frontend client, use the following command: streamlit run client.py