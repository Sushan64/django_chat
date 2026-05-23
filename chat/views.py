from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.db.models import Q

from . import models
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
  
def room(request, other_user_id):
  other_user = get_object_or_404(User, id=other_user_id)
  messages = models.ChatMessage.objects.filter(
    (Q(sender=request.user, receiver=other_user)) |
    (Q(sender=other_user, receiver=request.user))
    ).order_by('-timestamp')[:20]
    
  rev_messages = list(reversed(messages))
  return render(request, 'chat/room.html', {'other_user': other_user, "messages": rev_messages})