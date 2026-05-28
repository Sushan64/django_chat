from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse

from . import models
from .forms import SignupForm
from .decorators import check_friendship

# Create your views here.
def index(request):
  if request.user.is_authenticated:
    active_friends = models.Friendship.objects.filter(
      Q(sender=request.user) | Q(receiver=request.user),
      relation="active"
      ).exclude(Q(sender__username="AI_Assistant") | Q(receiver__username="AI_Assistant")).select_related('sender', 'receiver')
      
    pending_friends = models.Friendship.objects.filter(
      Q(sender=request.user) | Q(receiver=request.user),
      relation="pending"
      ).exclude(Q(sender__username="AI_Assistant") | Q(receiver__username="AI_Assistant")).select_related('sender','receiver')
    
    available_users = models.User.objects.exclude(
      friends_received__sender = request.user
      ).exclude(
        friends_sent__receiver = request.user
      ).exclude(
        id=request.user.id
      ).exclude(username="AI_Assistant")
    
    friends = []
    for friend in active_friends:
      if friend.sender == request.user:
        friends.append(friend.receiver)
      else:
        friends.append(friend.sender)
  else:
    friends=[]
    available_users=[]
    pending_friends=[]
  return render(request, 'chat/index.html', {
    'friends': friends,
    'pending_friends': pending_friends,
    'available_users': available_users,
  })
  
  
def add_friend(request):
  if request.method == "POST":
    user_id = request.POST.get('user_id')
    sender = User.objects.get(id=request.user.id)
    receiver = User.objects.get(id=user_id)
    friend, created = models.Friendship.objects.get_or_create(sender=sender, receiver=receiver)
    if created:
      return JsonResponse({'status': True, 'message': 'Friend request has been sent!'})
    return JsonResponse({'status': False, 'message': 'Something went wrong!'})
    
    
def accept_request(request):
  if request.method == "POST":
    user_id = request.POST.get('user_id')
    user = get_object_or_404(models.Friendship, sender__id=user_id, receiver__id=request.user.id)
    user.relation = "active"
    user.save(update_fields=['relation'])
    return JsonResponse({'status': True, 'message': 'You are now friends'})
  return JsonResponse({'status': False, 'message': 'Something went wrong'})
  
def signup(request):
  if request.method == "POST":
    form = SignupForm(request.POST)
    if form.is_valid():
      form.save()
      return redirect('/signin')
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
  if other_user_id != 0:
    other_user = get_object_or_404(User, id=other_user_id)
    # filter all the messages history as a sender or receiver
    messages = models.ChatMessage.objects.filter(
      (Q(sender=request.user, receiver=other_user)) |
      (Q(sender=other_user, receiver=request.user))
      ).order_by('-timestamp')[:20] # only last 20 messages to take
  else:
    ai_user = User.objects.get(username="AI_Assistant")
    other_user ={'id':0, 'username': 'AI Assistant'}
    messages = models.ChatMessage.objects.filter(
      (Q(sender=request.user, receiver=ai_user)) |
      (Q(sender=ai_user, receiver=request.user))
      ).order_by('-timestamp')[:20]
    
  rev_messages = list(reversed(messages))
  return render(request, 'chat/room.html', {'other_user': other_user, "messages": rev_messages})