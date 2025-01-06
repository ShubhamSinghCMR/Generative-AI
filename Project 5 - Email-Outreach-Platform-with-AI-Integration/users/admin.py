from django.contrib import admin

from .models import CustomUser, EmailTemplate, EmailTrack

# Register your models here
admin.site.register(CustomUser)
admin.site.register(EmailTemplate)
admin.site.register(EmailTrack)
