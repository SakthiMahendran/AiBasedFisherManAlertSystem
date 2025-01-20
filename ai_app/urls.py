from django.urls import path
from .views import ChatView

app_name = "ai"

urlpatterns = [
    path("weather/", ChatView.as_view(), name="chat"),           # New ChatView
]
