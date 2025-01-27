import logging
import os
import re
import subprocess
import tempfile
from io import BytesIO

import pandas as pd
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView
from faster_whisper import WhisperModel
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmailTemplate, EmailTrack
from .tasks import send_email_task
from .validators import validate_password_strength

logger = logging.getLogger(__name__)

model = WhisperModel("base", device="cpu")


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
            # Read the CSV file
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
                    "message": "File validated successfully.",
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

            # Check if the user is authenticated
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


class TemplateUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            template_id = request.data.get("template_id")
            updated_template = request.data.get("updated_template")

            # Check if the user is authenticated 
            if not request.user.is_authenticated:
                return Response(
                    {"error": "User must be authenticated to update a template."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if not template_id or not updated_template:
                return Response(
                    {"error": "Both template_id and updated_template are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve the template by ID and ensure the user owns it
            try:
                template = EmailTemplate.objects.get(
                    id=template_id, username=request.user
                )
            except EmailTemplate.DoesNotExist:
                return Response(
                    {
                        "error": "Template not found or you don't have permission to update it."
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Update the template content
            template.created_template = updated_template
            template.save()

            return Response(
                {
                    "message": "Template updated successfully.",
                    "template": template.created_template,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.error(f"Error updating template: {str(e)}")
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SendEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_pdf_file_path(self, pdf_file_name):
        try:
            file_path = default_storage.path(f"ai_attachments/{pdf_file_name}")
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File {pdf_file_name} not found in storage.")
            return file_path
        except Exception as e:
            print(f"Error retrieving PDF file: {e}")
            raise e

    def post(self, request):
        subject = request.data.get("subject")
        message = request.data.get("message")
        recipient_list = request.data.get("recipient_list")

        # Ensure recipient_list is a list and properly formatted
        if isinstance(recipient_list, str):
            recipient_list = (
                recipient_list.strip("[]").replace('"', "").split(",")
            )  # If it's a string, clean it
        elif isinstance(recipient_list, list):
            recipient_list = [
                email.strip() for email in recipient_list
            ]  # Strip any extra spaces in a list

        # Handle the Manual attachments
        attachments = request.FILES.getlist("attachments")  # Handling multiple files

        # Handle AI attachments (file names or URLs)
        pdf_attachments = request.data.getlist(
            "pdf_attachments"
        ) 

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
        print(f"reipient: {recipient_list}")

        # Validate email addresses
        valid_emails = []
        invalid_emails = []
        for email in recipient_list:
            try:
                # Regular expression for simple email validation
                regex = r"^[a-zA-Z0-9_.+-]+@([a-zAZ0-9-]+\.[a-zA-Z0-9-.]+)$"
               
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

        print(f"valid emails: {valid_emails}")

        print(f"invalid emails: {invalid_emails}")

        # Prepare the Manual attachment files
        attachment_files = []
        for file in attachments:
            file_path = default_storage.save(
                f"email_attachments/{file.name}", ContentFile(file.read())
            )
            attachment_files.append(file_path)

        print(f"PDF Attachments: {pdf_attachments}")
        
        # Handle AI attachments (assuming the front-end sends names or URLs)
        for pdf_file in pdf_attachments:
            try:
                file_path = self.get_pdf_file_path(
                    pdf_file
                )  # Fetch the correct file path
                if os.path.exists(file_path):  # Ensure the file exists
                    attachment_files.append(file_path)
                else:
                    print(f"PDF file not found: {pdf_file}")
            except Exception as e:
                print(f"Error retrieving PDF file: {pdf_file}, {e}")

        print(f"Starting Sending email after getting atachment...")
        print(f"Attachments: {attachment_files}")

        # Enqueue the email sending task
        try:
            send_email_task.delay(subject, message, valid_emails, attachment_files)
            # Log each valid email to EmailTrack model
            for email in valid_emails:
                EmailTrack.objects.create(
                    username=user,
                    recipient=email,
                    status="success",
                    subject=subject,
                    message=message,
                    attachments=[file.name for file in attachments],
                )
            for email in invalid_emails:
                EmailTrack.objects.create(
                    username=user,
                    recipient=email,
                    status="fail",
                    subject=subject,
                    message=message,
                    attachments=[file.name for file in attachments],
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


class AIGenerateTemplateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        description = request.data.get("description")

        if not description:
            return Response(
                {"error": "Description is required for generating suggestions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate AI email Template via Ollama
        try:
            template = self.generate_email_template(description)
            return Response(
                {
                    "template": template,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error generating content: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def generate_email_template(self, description):
        return self.generate_with_ollama(
            "Generate an email template with only the following placeholders: Receiver Name: {first_name}. Only generate the email body; do not include the subject, salutation, or any other elements. Do not conclude with phrases like 'Best Regards.' Simply return the email body. Topic: "
            + f"{description}"
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


class AIGenerateEmailAttachmentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        description = request.data.get("description")

        if not description:
            return Response(
                {"error": "Description is required for generating suggestions."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate AI email Attachment via Ollama
        try:
            attachment_content = self.generate_email_attachment(description)

            pdf_file = self.create_pdf(attachment_content, description)

            return Response(
                {
                    "message": "PDF attachment generated successfully.",
                    "attachment_url": pdf_file,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error generating content: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def generate_email_attachment(self, description):
        ai_prompt = (
            "Generate detailed content on the given topic. Please make sure the content is easy to understand, "
            "informative, and well-structured. Start by providing an introduction to the topic, then break it down into "
            "subtopics with clear explanations. Include examples, key points, and any relevant facts that will help the reader "
            "understand the topic thoroughly. Aim to provide a comprehensive overview that will be useful for someone who is "
            "new to this subject. "
            f"Topic: {description}"
        )
        return self.generate_with_ollama(ai_prompt)

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

    def create_pdf(self, content, description):
        # Create a PDF in memory
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Define margins in points (5 cm = 141.75 points)
        margin = 141.75
        top_margin = margin  # Top margin
        bottom_margin = margin  # Bottom margin
        left_margin = margin  # Left margin
        right_margin = margin  # Right margin

        # Set up basic content layout
        width, height = letter
        c.setFont("Helvetica", 12)

        # Add Heading (centered at the top with margin)
        heading = f"{description[:50]}"  
        heading_width = c.stringWidth(heading, "Helvetica", 12)
        c.drawString((width - heading_width) / 2, height - top_margin, heading)

        # Adjust starting point for content below the heading (leave space for the heading)
        y_position = height - top_margin - 20  # 20px space after heading

        # Set up styles for text formatting and paragraph wrapping
        style = getSampleStyleSheet()["Normal"]
        style.fontName = "Helvetica"
        style.fontSize = 10
        style.leading = 12
        style.alignment = 0  # Align text to the left

        # Wrap the content text to fit within the page width (left to right margins)
        max_width = width - left_margin - right_margin  # Calculate max width

        # Create a paragraph object to handle line breaks and word wrapping
        text_paragraph = Paragraph(content, style)

        # Adjust wrap space for the content
        text_paragraph.wrap(
            max_width, height - top_margin - 40
        )  # 40px space for heading and some margin
        text_paragraph.drawOn(c, left_margin, y_position)

        # Adjust y_position after the content is drawn
        y_position -= text_paragraph.height

        # Handle pagination if content exceeds one page
        while y_position > bottom_margin and text_paragraph.height > 0:
            # Check if we need to move to the next page
            if y_position - text_paragraph.height < bottom_margin:
                c.showPage()  # Start a new page
                y_position = (
                    height - top_margin - 20
                )  # Reset Y position for the new page

                # Add heading again on the new page
                c.setFont("Helvetica", 12)
                c.drawString((width - heading_width) / 2, height - top_margin, heading)

                # Rewrap the content for the new page
                text_paragraph.wrap(max_width, height - top_margin - 40)

            # Draw the wrapped content for the current page
            text_paragraph.drawOn(c, left_margin, y_position)
            y_position -= (
                text_paragraph.height
            )  # Update the position for the next text block

        c.showPage()
        c.save()

        # Save the PDF in memory and return the file path or response
        buffer.seek(0)
        file_name = description[0:20] + ".pdf"
        pdf_dir = os.path.join(
            settings.BASE_DIR, "ai_attachments"
        )  

        # Ensure the directory exists
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        pdf_file_path = os.path.join(pdf_dir, file_name)
        with open(pdf_file_path, "wb") as f:
            f.write(buffer.getvalue())

        buffer.close()

        # Return the file path (relative for front-end purposes)
        return f"/ai_attachments/{file_name}"


class PdfAttachmentsView(View):
    def get(self, request, *args, **kwargs):
        # Define the attachments folder path
        attachments_folder = os.path.join(settings.BASE_DIR, "ai_attachments")

        # Check if the attachments folder exists
        if not os.path.exists(attachments_folder):
            return JsonResponse(
                {"pdf_files": [], "message": "Attachments folder not found."},
                status=404,
            )

        # List all PDF files in the attachments folder with corrected URLs
        pdf_files = [
            {
                "name": f,
                "url": request.build_absolute_uri(
                    f"/ai_attachments/{f}"  # Corrected URL path
                ),
            }
            for f in os.listdir(attachments_folder)
            if f.endswith(".pdf")
        ]

        # Return the list of files as a JSON response
        return JsonResponse({"pdf_files": pdf_files})


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
            "recipient", "subject", "email_sent_date", "message", "attachments"
        )
        fail_list = failed_emails.values(
            "recipient", "subject", "email_sent_date", "message", "attachments"
        )

        response_data = {
            "success_count": success_count,
            "fail_count": fail_count,
            "successful_emails": list(success_list),
            "failed_emails": list(fail_list),
        }

        return Response(response_data, status=200)


class SpeechToTextView(View):
    def post(self, request):
        print("REQUESTED")
        if not request.FILES.get("audio"):
            return JsonResponse({"error": "No audio file provided."}, status=400)

        audio_file = request.FILES["audio"]

        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        try:
            # Transcribe the audio
            segments, _ = model.transcribe(temp_file_path)
            transcription = "".join([segment.text for segment in segments])

            return JsonResponse({"transcription": transcription})

        except Exception as e:
            return JsonResponse(
                {"error": f"Error during transcription: {str(e)}"}, status=500
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
