import os
import asyncio
import logging
import json
from dotenv import load_dotenv
import re
from groq import Groq

# Load environment variables
load_dotenv()

# Set the logging level for httpx to WARNING to suppress INFO level logs
logging.getLogger("httpx").setLevel(logging.WARNING)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Function to parse the LLM response and convert it to JSON
def parse_llm_response(response):
    try:
        entities = re.findall(r"'\s*(.*?)\s*'", re.search(r"entityList = \[(.*?)\]", response).group(1))
        parameters = re.findall(r"'\s*(.*?)\s*'", re.search(r"parameterList = \[(.*?)\]", response).group(1))
        start_dates = re.findall(r"'\s*(.*?)\s*'", re.search(r"startDate = \[(.*?)\]", response).group(1))
        end_dates = re.findall(r"'\s*(.*?)\s*'", re.search(r"endDate = \[(.*?)\]", response).group(1))

        json_output = []
        for entity in entities:
            for param, start, end in zip(parameters, start_dates, end_dates):
                json_output.append({
                    "entity": entity,
                    "parameter": param,
                    "startDate": start,
                    "endDate": end
                })

        return json.dumps(json_output, indent=4)

    except Exception as e:
        logger.error(f"Error parsing LLM response: {str(e)}")
        return f"Error while parsing the response: {str(e)}"

# Async function to query LLM 
async def get_llm_response(prompt: str):
    try:
        chat_completion = await asyncio.to_thread(client.chat.completions.create, 
                                                  messages=[{"role": "user", "content": prompt}],
                                                  model="llama-3.1-8b-instant")

        return chat_completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Error during LLM processing: {str(e)}")
        return None

# Main function to handle user input, simulate chatbot conversation flow
def main():
    print("LLM-Powered Application!")
    print("You can ask questions about company performance metrics.")

    while True:
        # Ask for user input (one question at a time)
        user_input = input("Enter your query (or type 'exit' to quit): ")
        
        if user_input.lower() == "exit":
            print("Have a good day! Bye!")
            break

        # Prompt for the LLM
        prompt = f"""
        You are a data extraction assistant. Given a user query, your task is to extract and structure the following information:

        1. **Entity (Company Name)**: Extract the company name(s) mentioned in the query (e.g., Flipkart, Amazon).
        2. **Parameter (Performance Metric)**: Extract the performance metric mentioned in the query (e.g., GMV, revenue, profit).
        3. **Date Range**:
            - Extract the start and end dates of the period for which the metric is requested.
            - If expressions like 'quarter', '6 months', 'year', etc., or relative terms are provided, calculate the appropriate dates.
            - If expressions like 'last year', 'last month', 'past year', 'last six months', 'last quarter', etc., are used, interpret "last" as referring to the **previous calendar period**. 
                - "Last year" or "Past year" refers to the **previous calendar year** (e.g., if the current year is 2024, last year refers to 2023).
                - "Last month" refers to the **previous month** (e.g., if the current month is December 2024, last month refers to November 2024).
                - "Last quarter" refers to the **previous quarter** (e.g., If current quarter is Q2, it means that last quarter was Q1).
                - "Last six months" refers to the **six months immediately preceding the current month**.
            - If the user query does not explicitly mention the start date and/or end date, assume the following defaults:
                - Start Date: Today's date minus one year.
                - End Date: Today's date.

        Please provide the output **strictly in the following format**. Do not change the format or provide any extra information:

        entityList = ['company1 name','company2 name','company3 name' and so on]
        parameterList = ['paramter1 name','parameter 2 name','parameter 3 name' and so on]
        startDate = ['yyyy-mm-dd']
        endDate = ['yyyy-mm-dd']

        Here is the user query you need to process:
        "{user_input}"
        """

        # Call the async function to get LLM response for the current query
        llm_response = asyncio.run(get_llm_response(prompt))

        if llm_response:
            # Convert LLM response to JSON format
            json_output = parse_llm_response(llm_response)

            # Display the JSON output
            print(json_output)
        else:
            logger.error("Error retrieving LLM response.")

if __name__ == "__main__":
    main()
