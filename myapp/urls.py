from django.urls import path
from . import views

urlpatterns = [
    path("", views.BlankHome, name="Blankhome"),
    path("Welcome/",views.home, name="home"),
    path("todos/", views.todos, name="Todos"),
    path("AboutUs/", views.AboutUs, name="AboutUs"),
    path("Results/", views.Results, name="Results"),
    path("Sounds/", views.Sounds, name="Sounds")
]