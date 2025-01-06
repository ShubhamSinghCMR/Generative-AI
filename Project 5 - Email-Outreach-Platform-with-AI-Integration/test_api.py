import requests

# Base URL for API
BASE_URL = "http://127.0.0.1:8000/api/users/"

# User credentials for registration and login
USER_DATA = {"username": "temp123", "password": "Temp@1pass"}

# Template for email
TEMPLATE = "Hello {first_name}, welcome to our platform!"

# Data for sending the email
email_data = {
    "subject": "Test Email",
    "message": "This is a test email sent from Django.",
    "recipient_list": [
        "user1@gmaail.com",
        "user2@gmail.com",
        "user3@gmail.com",
    ],
}

# AI Input
ai_data = {"description": "New Year Sale"}


# Register a New User
def test_register():
    data = {"username": USER_DATA["username"], "password": USER_DATA["password"]}
    response = requests.post(f"{BASE_URL}register/", json=data)
    print("Register Response:", response.status_code, response.json())
    if response.status_code == 201:
        print("Status: Registered")
    else:
        print("Status: Error")


# Login with the Registered User
def test_login(session):
    data = {"username": USER_DATA["username"], "password": USER_DATA["password"]}
    response = session.post(f"{BASE_URL}login/", json=data)
    print("Login Response:", response.status_code, response.json())
    if response.status_code == 200:
        print("Status: Logged in")
        return session
    else:
        print("Status: Invalid credentials")
        return None


# Logout the User
def test_logout(session, csrf_token):
    headers = {"X-CSRFToken": csrf_token}
    response = session.post(f"{BASE_URL}logout/", headers=headers)
    if response.status_code == 205:
        print("Logout Response:", response.status_code)
        print("Status: Logged out")
    else:
        print("Logout Response:", response.status_code, response.text)
        print("Status: Error")


# Test CSV Upload
def test_csv_upload(session, csrf_token):
    with open("testcsv2.csv", "rb") as file:
        headers = {"X-CSRFToken": csrf_token}
        response = session.post(
            f"{BASE_URL}csv-validation/", files={"file": file}, headers=headers
        )
    print("CSV Upload Response:", response.status_code, response.json())


# Test Template Creation
def test_template_creation(session, csrf_token):
    data = {"template": TEMPLATE}
    headers = {"X-CSRFToken": csrf_token}
    response = session.post(f"{BASE_URL}template/", json=data, headers=headers)
    print("Template Response:", response.status_code, response.json())


# Send Test Mail
def test_send_email(session, csrf_token):
    headers = {"X-CSRFToken": csrf_token}
    response = session.post(f"{BASE_URL}send-email/", json=email_data, headers=headers)

    if response.status_code == 200:
        print("Email sending started.")
        print("Sent to valid emails:", response.json().get("sent_to"))
        print("Not sent to invalid emails:", response.json().get("not_sent_to"))
    else:
        print("Error sending email:", response.status_code, response.json())


# Function for AI suggestions
def ai_suggestion_email(session, csrf_token, data):
    headers = {"X-CSRFToken": csrf_token}
    response = session.post(f"{BASE_URL}ai-suggestions/", json=data, headers=headers)

    if response.status_code == 200:
        print("Generated Subject:", response.json()["subject"])
        print("Generated Body:", response.json()["body"])
    else:
        print("Error in AI Suggestion:", response.status_code, response.json())


# Test Get User Templates
def test_user_templates(session):
    response = session.get(f"{BASE_URL}get-user-templates/")
    print("User Templates Response:", response.status_code, response.json())
    if response.status_code == 200:
        print("Templates retrieved:", response.json()["templates"])
    else:
        print("Error retrieving templates:", response.status_code, response.json())


# Test Get Email Status
def test_email_status(session, csrf_token):
    headers = {"X-CSRFToken": csrf_token}
    response = session.get(f"{BASE_URL}email-status/", headers=headers)

    if response.status_code == 200:
        print("Email Status Response:", response.status_code)
        print("Number of Successful Emails:", response.json().get("success_count"))
        print("Number of Failed Emails:", response.json().get("fail_count"))
        print("Successful Emails:", response.json().get("successful_emails"))
        print("Failed Emails:", response.json().get("failed_emails"))
    else:
        print("Error fetching email status:", response.status_code, response.json())


if __name__ == "__main__":
    # Create a session to manage cookies
    session = requests.Session()

    print("Testing Registration:")
    test_register()

    print("\nTesting Login:")
    session = test_login(session)

    if session:
        # Extract the CSRF token from the session cookies
        csrf_token = session.cookies.get("csrftoken")

        if csrf_token:
            print("\nTesting CSV Upload:")
            test_csv_upload(session, csrf_token)

            print("\nTesting Template Creation:")
            test_template_creation(session, csrf_token)

            print("\nTesting Email Send:")
            test_send_email(session, csrf_token)

            print("\nTesting Email Status:")
            test_email_status(session, csrf_token)

            print("\nTesting AI Email Suggestions:")
            ai_suggestion_email(session, csrf_token, ai_data)

            print("\nTesting User Templates:")
            test_user_templates(session)

            print("\nTesting Logout:")
            test_logout(session, csrf_token)
        else:
            print("CSRF Token missing, aborting further tests.")
    else:
        print("Login failed, skipping further tests.")
