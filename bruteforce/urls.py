from django.contrib import admin
from tasks import *
from django.urls import path

urlpatterns = [
    path("", admin.site.urls),
]
