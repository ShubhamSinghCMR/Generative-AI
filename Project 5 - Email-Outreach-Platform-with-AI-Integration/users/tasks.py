import logging
from time import sleep

from celery import shared_task
from django.conf import settings
from django.core.files import File
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(subject, message, valid_emails, attachments=None):
    print(f"Starting Sending email...")
    try:
        for email in valid_emails:
            logger.info(f"Sending email to {email}")
            print(f"Sending email to {email}")

            # Create an email message object
            email_message = EmailMessage(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # Sender email
                [email],  # Recipient email
            )

            # Add attachments if any
            if attachments:
                for file in attachments:
                    # Assuming `file` is the path to the saved file
                    email_message.attach_file(file)

            # Send the email
            email_message.send(fail_silently=False)

            logger.info(f"Email sent to {email}")
            print(f"Email sent to {email}")

            # Introduce a delay between sending each email
            logger.info("Waiting for 2 seconds before sending next email...")
            sleep(2)
            logger.info("Resuming email sending...")

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        print(f"Error sending email: {str(e)}")
        return f"Failed to send email: {str(e)}"
