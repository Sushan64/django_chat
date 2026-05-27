from . import models
from django.db.models import Q
from django.shortcuts import redirect

'''
DECORATORS is a special function which
takes another functions as an arguments.
Decorators functions runs before or after the
arguments functions.
'''


'''
This is the check_friendship decorators function.
It accept a function argument, validate the user friendship in DB,
and decide permission for request.user to chat with other user or not.
'''
def check_friendship(fun):
  # This is the inner wrapper function, it holds the arguments of orginal func
  def wrapper(req, other_user_id, *args, **kwargs):
    if other_user_id != 0:   # 0 means AI Chat bot, ignore validation
      is_friend = models.Friendship.objects.filter(
        Q(sender_id=req.user.id, receiver_id=other_user_id) |
        Q(sender_id=other_user_id, receiver_id=req.user.id),
        relation="active"
      ).exists()
      if not is_friend:
        return redirect('/')
    return fun(req, other_user_id)
  return wrapper