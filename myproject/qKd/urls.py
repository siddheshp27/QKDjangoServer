# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.createQuantumKeys, name='home'),
]
