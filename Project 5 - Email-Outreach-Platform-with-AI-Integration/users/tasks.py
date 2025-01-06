import logging
from time import sleep

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task
def send_email_task(subject, message, valid_emails):
    try:
        for email in valid_emails:
            logger.info(f"Sending email to {email}")

            # Send the email
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,  # Sender email
                [email],  # Recipient email
                fail_silently=False,  # Fail if there's an error
            )

            logger.info(f"Email sent to {email}")

            # Introduce a delay between sending each email
            logger.info("Waiting for 2 seconds before sending next email...")
            sleep(2)
            logger.info("Resuming email sending...")

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return f"Failed to send email: {str(e)}"
