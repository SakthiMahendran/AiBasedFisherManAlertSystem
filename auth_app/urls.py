from django.urls import path
from .views import SignUpView, LoginView

app_name = 'auth_app'

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
]
