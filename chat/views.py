from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from . import models
from .forms import SignupForm


def check_friendship(fun):
  def wrapper(req, other_user_id):
    is_friend = models.Friendship.objects.filter(
      Q(sender_id=req.user.id, receiver_id=other_user_id) |
      Q(sender_id=other_user_id, receiver_id=req.user.id),
      relation="active"
    ).exists()
    if not is_friend:
      return redirect('/')
    return fun(req, other_user_id)
  return wrapper
  
# Create your views here.
def index(request):
  if request.user.is_authenticated:
    active_friends = models.Friendship.objects.filter(
      Q(sender=request.user) | Q(receiver=request.user),
      relation="active"
      ).select_related('sender', 'receiver')
      
    pending_friends = models.Friendship.objects.filter(
      Q(sender=request.user) | Q(receiver=request.user),
      relation="pending"
      ).select_related('sender','receiver')
    
    available_users = models.User.objects.exclude(
      friends_received__sender = request.user
      ).exclude(
        friends_sent__receiver = request.user
      ).exclude(
        id=request.user.id
      )
    
    friends = []
    for friend in active_friends:
      if friend.sender == request.user:
        friends.append(friend.receiver)
      else:
        friends.append(friend.sender)
  else:
    friends=[]
  return render(request, 'chat/index.html', {
    'friends': friends,
    'pending_friends': pending_friends,
    'available_users': available_users,
  })
  
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

  
@login_required
def signout(request):
  logout(request)
  return redirect('/')
 
@login_required
@check_friendship
def room(request, other_user_id):
  other_user = get_object_or_404(User, id=other_user_id)
  messages = models.ChatMessage.objects.filter(
    (Q(sender=request.user, receiver=other_user)) |
    (Q(sender=other_user, receiver=request.user))
    ).order_by('-timestamp')[:20]
    
  rev_messages = list(reversed(messages))
  return render(request, 'chat/room.html', {'other_user': other_user, "messages": rev_messages})