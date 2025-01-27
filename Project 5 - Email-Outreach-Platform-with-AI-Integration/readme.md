# Project Summary: Email Outreach Platform with AI Integration
The project is an AI-powered Email Outreach Platform designed to streamline email campaign management with features like user authentication, CSV-based bulk email uploads, and AI-driven email suggestions.

## Key Features:
- **User Authentication:** Secure sign-up, login, and logout functionality.
- **Campaign Creation:** Upload recipient details via CSV, create customizable email templates with dynamic placeholders.
- **Email Delivery:** Send emails using Gmail server, with queuing and error handling.
- **AI Integration:** Leverage AI to suggest subject lines and email body text based on campaign descriptions.
- **Dashboard Metrics:** Track and display campaign performance (e.g., sent and failed emails).
- **Validation and Logging:** Validate inputs (e.g., email format) and log errors for debugging and performance monitoring.

This platform simplifies email outreach and enhances campaign personalization using AI insights.

---

# AI Integration:
The platform utilizes the Llama3.2 AI model to generate email content. The idea is provided as a prompt to the AI, which then generates both the subject line and email body dynamically based on the given input. This integration helps streamline the content creation process and allows users to quickly generate professional email drafts for their campaigns.

---

# Setup and Installation instructions (Windows): 

# # 1.	Clone the Repository
1. Open your browser and visit the repository: https://github.com/ShubhamSinghCMR/Generative-AI.git
2. Clone it using the following command in your terminal:
```
git clone https://github.com/ShubhamSinghCMR/Generative-AI.git
```

# # 2.	Create a Virtual Environment
Run the following command to create a virtual environment:
```
python -m venv venv
```

# # 3.	Activate the Virtual Environment
Activate the virtual environment:
```
venv\Scripts\activate
```

# # 4.	Install Project Requirements
Install the dependencies using:
```
pip install -r requirements.txt
```

# # 5.	Open the Project Folder
Navigate to the cloned project directory:
```
cd 'Project 5 - Email-Outreach-Platform-with-AI-Integration'
```

# # 6.	Install and Configure Redis
1. Download the Redis installer (e.g., Redis-x64-3.0.504.msi) from: https://github.com/microsoftarchive/redis/releases.
2. Install Redis and open the installation folder (e.g., C:\Redis) in a new terminal. Run the following command:
```
redis-server --port 6380
```
3. On successful execution, you will see Redis running.

# # 7.	Run Celery
1. In your project folder, run Celery with:
```
celery -A email_outreach.celery worker --loglevel=info --pool=solo
```
2. Celery will start running successfully.

# # 8.	Install and Run Ollama
1. Download and install Ollama from: https://ollama.com/download.
2. Open the terminal and pull the model:
```
ollama pull llama3.2
```
3. Run the server with:
```
ollama run llama3.2
```
Alternatively, start the Ollama app from the Start menu to run the server automatically.

# # 9.	Configure Email Credentials
Set up your email credentials (Gmail ID and App Password) in the .env file located in the project folder.
To generate your app password, visit: https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://myaccount.google.com/apppasswords&ved=2ahUKEwi25vTzhteKAxVEyDgGHTzoMwIQFnoECBgQAQ&usg=AOvVaw1rVibBR6kQTiUjqa0l_f8W

# # 10.	Run Migrations and Start the Project
1. Open a new terminal, activate the virtual environment, and run:
```
python manage.py makemigrations
python manage.py migrate
```
2. Start the server:
```
python manage.py runserver
```

# # 11.	Access the Application
Open your browser and navigate to:
```
http://127.0.0.1:8000/
```

# # 12.	Create a New User
Use the "Signup" option on the webpage to create a new user.

# # 13.	Log In and Explore the Project
Sign in with the credentials you created and explore the application.

# # 14.	Access Admin Panel
To view or manage data in the database, visit:
```
http://127.0.0.1:8000/admin/
```
Use the following admin credentials:
- Username: admin1
- Password: admin1

---

# Known Limitations or Assumptions
- AI Content Generation:
The quality and relevance of the generated subject line and email body depend on the clarity and specificity of the input prompt. Vague or ambiguous descriptions might lead to less relevant outputs. The model might not always generate perfectly tailored content, and manual adjustments might still be necessary.

- Email Delivery: 
The email delivery system relies on external service (Gmail) and could face limitations in terms of send volume, rate limits, or blocked emails due to poor sender reputation.

- File Format Validation:
The system assumes that uploaded CSV files are formatted correctly. Invalid files (e.g., missing required fields or improper formatting) will lead to errors during the upload process.

- Internet Connectivity:
The AI model and email service integrations require a stable internet connection for generating content and sending emails.

---

# Screenshots:
![Screenshot 2025-01-02 152621](https://github.com/user-attachments/assets/2f7c4588-3529-473f-9be2-8b8579fe4042)

![Screenshot 2025-01-02 152641](https://github.com/user-attachments/assets/72a916d8-4d9a-4ef3-a15e-e868aad7e333)

![Screenshot 2025-01-02 152612](https://github.com/user-attachments/assets/c5781d1b-cbbe-454d-8404-57641cdeec12)

![Screenshot 2025-01-02 152516](https://github.com/user-attachments/assets/f2b856a3-2c4f-40b0-b572-47149f196b62)
