import logging
import re
import subprocess

import pandas as pd
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmailTemplate, EmailTrack
from .tasks import send_email_task
from .validators import validate_password_strength

logger = logging.getLogger(__name__)


class WelcomePageView(TemplateView):
    template_name = "index.html"


class SigninPageView(TemplateView):
    template_name = "signin.html"


class SignupPageView(TemplateView):
    template_name = "signup.html"


class HomeView(TemplateView):
    template_name = "home.html"


class SendEmailPageView(TemplateView):
    template_name = "send-email.html"


class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        email = request.data.get("email")

        # Check if username and password are provided
        if not username or not password:
            return Response(
                {"error": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user already exists
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "User already exists."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_password_strength(password)
        except ValidationError as e:
            errors = e.messages
            return Response(
                {
                    "error": "Password is not strong enough.",
                    "details": errors,
                    "guidelines": [
                        "Password must be at least 8 characters long.",
                        "Password must contain both uppercase and lowercase letters.",
                        "Password must contain at least one numeric digit.",
                        "Password must contain at least one special character.",
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create the user
        User = get_user_model()
        User.objects.create_user(username=username, password=password, email=email)
        return Response(
            {"message": "User registered successfully."}, status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        # Authenticate the user
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)

            return Response(
                {
                    "message": "Login successful",
                    "loggeduserinx": user.username,
                },
                status=status.HTTP_200_OK,
            )

        # Invalid credentials
        return Response(
            {"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    def post(self, request):
        try:
            logout(request)  # This clears the session for the user
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            logger.error(
                f"Error during logout for user {request.user.username}: {str(e)}"
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CSVUploadView(TemplateView):
    template_name = "csv_validation.html"


class CSVValidationView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return JsonResponse({"error": "No file uploaded."}, status=400)

        try:
            # Read the CSV file using pandas
            df = pd.read_csv(file)

            # Define required columns
            required_columns = ["email", "first_name"]
            errors = []

            # Check for missing required columns
            for column in required_columns:
                if column not in df.columns:
                    errors.append(f"Missing required column: {column}")

            # Check for extra columns
            extra_columns = [col for col in df.columns if col not in required_columns]
            if extra_columns:
                errors.append(f"Extra columns found: {', '.join(extra_columns)}")

            if errors:
                return JsonResponse({"error": errors}, status=400)

            return JsonResponse(
                {
                    "message": "File uploaded and validated successfully.",
                    "data": df.to_dict(orient="records"),
                },
                status=200,
            )

        except Exception as e:
            return JsonResponse({"error": [str(e)]}, status=400)


class CheckAuthenticationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            return Response(
                {"message": "User is authenticated", "username": request.user.username},
                status=200,
            )
        else:
            return Response({"message": "User is not authenticated"}, status=401)


class CreateTemplateView(TemplateView):
    template_name = "template-create.html"


class TemplateEditorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            template = request.data.get("template")

            # Check if the user is authenticated (session will automatically be checked)
            if not request.user.is_authenticated:
                return Response(
                    {"error": "User must be authenticated to create a template."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not template:
                return Response(
                    {"error": "Template is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Save the template to the database
            new_template = EmailTemplate.objects.create(
                username=request.user, created_template=template
            )
            new_template.save()

            return Response(
                {
                    "message": "Template created successfully.",
                    "template": new_template.created_template,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SendEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        subject = request.data.get("subject")
        message = request.data.get("message")
        recipient_list = request.data.get("recipient_list")

        # Validate the input
        if not subject or not message or not recipient_list:
            return Response(
                {"error": "Subject, message, and recipient list are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Define valid domains
        valid_domains = [
            "gmail.com",
            "yahoo.com",
            "outlook.com",
        ]

        # Get the current user
        user = request.user

        # Validate email addresses
        valid_emails = []
        invalid_emails = []
        for email in recipient_list:
            try:
                # Regular expression for simple email validation
                regex = r"^[a-zA-Z0-9_.+-]+@([a-zAZ0-9-]+\.[a-zA-Z0-9-.]+)$"
                # Simple email format validation
                match = re.match(regex, email)
                if match:
                    domain = match.group(1)
                    if domain in valid_domains:  # Check if domain is valid
                        valid_emails.append(email)
                    else:
                        invalid_emails.append(email)
                else:
                    invalid_emails.append(email)
            except Exception as e:
                print("Error: ", e)
                invalid_emails.append(email)

        # Enqueue the email sending task using Celery
        try:
            send_email_task.delay(subject, message, valid_emails)
            # Log each valid email to EmailTrack model
            for email in valid_emails:
                EmailTrack.objects.create(
                    username=user,
                    recipient=email,
                    status="success",
                    subject=subject,
                    message=message,
                )
            for email in invalid_emails:
                EmailTrack.objects.create(
                    username=user,
                    recipient=email,
                    status="fail",
                    subject=subject,
                    message=message,
                )
        except Exception as e:
            print("Error: ", e)

        # Return the response showing emails sent and failed ones
        response_data = {
            "message": "Email sending started. Emails will be sent asynchronously.",
            "sent_to": valid_emails,
            "not_sent_to": invalid_emails,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class AIGenerateSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        description = request.data.get("description")

        if not description:
            return Response(
                {"error": "Description is required for generating suggestions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate AI email subject and body via Ollama
        try:
            subject = self.generate_email_subject(description)
            body = self.generate_email_body(description)
            return Response(
                {
                    "subject": subject,
                    "body": body,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error generating content: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def generate_email_subject(self, description):
        return self.generate_with_ollama(
            f"Generate a one-line email subject within 10 words for: : {description}"
        )

    def generate_email_body(self, description):
        return self.generate_with_ollama(
            f"Do not create subject. Write an email body for: {description}"
        )

    def generate_with_ollama(self, prompt):
        # Run the Ollama command in subprocess
        try:
            result = subprocess.run(
                ["ollama", "run", "llama3.2", prompt],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error running Ollama: {str(e)}")


class UserTemplatesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get all templates for the current logged-in user
            templates = EmailTemplate.objects.filter(username=request.user)

            template_data = [
                {"id": template.id, "created_template": template.created_template}
                for template in templates
            ]

            return Response({"templates": template_data}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(
                f"Error fetching templates for user {request.user.username}: {str(e)}"
            )
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EmailStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the current user
        user = request.user

        # Query the EmailTrack model for the current user's email statuses
        successful_emails = EmailTrack.objects.filter(username=user, status="success")
        failed_emails = EmailTrack.objects.filter(username=user, status="fail")

        # Count the number of successful and failed emails
        success_count = successful_emails.count()
        fail_count = failed_emails.count()

        # Get the details of successful and failed emails
        success_list = successful_emails.values(
            "recipient", "subject", "email_sent_date", "message"
        )
        fail_list = failed_emails.values(
            "recipient", "subject", "email_sent_date", "message"
        )

        response_data = {
            "success_count": success_count,
            "fail_count": fail_count,
            "successful_emails": list(success_list),
            "failed_emails": list(fail_list),
        }

        return Response(response_data, status=200)
