import os

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import (AIGenerateEmailAttachmentView, AIGenerateSuggestionsView,
                    AIGenerateTemplateView, CheckAuthenticationView,
                    CreateTemplateView, CSVUploadView, CSVValidationView,
                    EmailStatusView, HomeView, LoginView, LogoutView,
                    PdfAttachmentsView, RegisterView, SendEmailPageView,
                    SendEmailView, SigninPageView, SignupPageView,
                    SpeechToTextView, TemplateEditorView, TemplateUpdateView,
                    UserTemplatesView, WelcomePageView)

urlpatterns = [
    path("", WelcomePageView.as_view(), name="welcome-page"),
    path("signup/", SignupPageView.as_view(), name="signup-page"),
    path("register/", RegisterView.as_view(), name="register"),
    path("signin/", SigninPageView.as_view(), name="signin-page"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("home/", HomeView.as_view(), name="home"),
    path("csv-validation/", CSVValidationView.as_view(), name="csv_validation"),
    path("upload-csv/", CSVUploadView.as_view(), name="upload-csv"),
    path("create-template/", CreateTemplateView.as_view(), name="create-template"),
    path("template/", TemplateEditorView.as_view(), name="template-editor"),
    path("send-email/", SendEmailView.as_view(), name="send-email"),
    path("updatetemplate/", TemplateUpdateView.as_view(), name="update-template"),
    path("ai-suggestions/", AIGenerateSuggestionsView.as_view(), name="ai-suggestions"),
    path(
        "ai-attachment/", AIGenerateEmailAttachmentView.as_view(), name="ai-attachment"
    ),
    path(
        "get-pdf-attachments/", PdfAttachmentsView.as_view(), name="get_pdf_attachments"
    ),
    path(
        "check-authentication/",
        CheckAuthenticationView.as_view(),
        name="check-authentication",
    ),
    path("send-email-page/", SendEmailPageView.as_view(), name="send-email-page"),
    path("get-user-templates/", UserTemplatesView.as_view(), name="get-user-templates"),
    path("email-status/", EmailStatusView.as_view(), name="email-status"),
    path("speech-to-text/", SpeechToTextView.as_view(), name="speech-to-text"),
    path("ai-template/", AIGenerateTemplateView.as_view(), name="ai-template"),
]

# ai_attachments folder 
if settings.DEBUG:
    urlpatterns += static(
        "/ai_attachments/",  
        document_root=os.path.join(
            settings.BASE_DIR, "ai_attachments"
        ),  
    )
