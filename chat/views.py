from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignupForm

# Create your views here.
def index(request):
  return render(request, 'chat/index.html')
  
def signup(request):
  if request.method == "POST":
    form = SignupForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('/')
  else:
    form = SignupForm()
  
  return render(request, 'chat/signup.html', {'form': form})


def signin(request):
  if request.method == "POST":
    username = request.POST["username"]
    password = request.POST["password"]
    user = authenticate(username=username, password=password)
    if user is not None:
      login(request, user)
      return redirect('/')
    else:
      return render(request, 'chat/signin.html', {'error': 'Invalid credentials'})
  return render(request, 'chat/signin.html')
  
  
def signout(request):
  logout(request)
  return redirect('/')
  
def room(request, room_name):
  return render(request, 'chat/room.html', {'room': room_name})