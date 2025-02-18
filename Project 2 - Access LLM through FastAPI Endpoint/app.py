from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM as Ollama
from langchain_core.output_parsers import StrOutputParser
from langserve import add_routes

from fastapi import FastAPI
import uvicorn

app = FastAPI()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system","Answer the user queries"),
        ("user","{question}")
    ]

)

llm = Ollama(model="llama3.2")

output=StrOutputParser()

add_routes(
    app,
    prompt | llm | output,
    path = "/ask"
)

uvicorn.run(app)

