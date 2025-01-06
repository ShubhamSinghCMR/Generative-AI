# Problem:
To create a LLM-powered application that takes user queries related to company performance metrics and converts them into a structured JSON format.

# Requirements:
1. Use llama-3.1-8b-instant model from https://console.groq.com/

2. The application should be able to extract the following information from user queries:
    - Entity: The company name mentioned in the query (e.g., Flipkart, Amazon).
    - Parameter: The performance metric mentioned in the query (e.g., GMV, revenue, profit).
    - Start Date: The start date of the time period for which the metric is requested.
    - End Date: The end date of the time period for which the metric is requested.

3. If the user query does not explicitly mention the start date and/or end date, assume the following defaults:
    - Start Date: Today's date minus one year.
    - End Date: Today's date.

4. The extracted information should be converted into a JSON format with the following structure:

[
    {
        "entity": "Tesla",
        "parameter": "profit",
        "startDate": "2024-06-01",
        "endDate": "2024-08-31"
    }
]

5. If the user query mentions multiple companies or requests a comparison, the JSON output should include multiple objects, one for each company mentioned.

[
    {
        "entity": "Amazon",
        "parameter": "profits",
        "startDate": "2023-01-01",
        "endDate": "2023-12-31"
    },
    {
        "entity": "Flipkart",
        "parameter": "profits",
        "startDate": "2023-01-01",
        "endDate": "2023-12-31"
    }
]

6. The start date and end date should be converted to the ISO 8601 format (YYYY-MM-DD) before including them in the JSON output.

7. Use a combination of LLM calls and Python code to accomplish the task. The LLM can be used to understand the user query and extract relevant information, while Python can be used for data manipulation and JSON conversion.

# Additional Considerations:

- Handle variations in user queries, such as different spellings or abbreviations of company names and metric parameters.
- Implement error handling for cases where the LLM fails to extract the necessary information from the user query.
- Consider adding support for additional date formats or relative date ranges (e.g., "last quarter", "previous month").

# Execution Instructions:

Prerequisites:
1. Python Version: Ensure Python 3.8 or later is installed.
2. Jupyter Notebook: Install Jupyter Notebook or JupyterLab for running Python scripts interactively.

Next Steps: 
1. To ensure the application runs smoothly, execute all cells in the notebook in the given sequence.
2. This step-by-step execution will help avoid any errors and ensure proper initialization of dependencies, environment variables, and functions.
