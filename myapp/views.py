from django.shortcuts import redirect, render, HttpResponse
from .models import TodoItem

# Create your views here.
def home(request):
    return render(request, "home.html")

def todos(request):
    items = TodoItem.objects.all()
    return render(request, "todos.html", {"todos": items})

def BlankHome(request):
    return redirect(home)

def AboutUs(request):
    return render(request, "AboutUs.html")

def Sounds(request):
    return render(request, "Sounds.html")