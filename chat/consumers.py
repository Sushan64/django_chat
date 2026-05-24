import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import ChatMessage, Friendship
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.defaultfilters import date as django_date
from django.db.models import Q

class ChatConsumer(AsyncWebsocketConsumer):
  async def connect(self):
    self.user = self.scope['user']
    if not self.user.is_authenticated:
      await self.close()
      return
    
    self.other_user_id = self.scope['url_route']['kwargs']['other_user_id']
    users_id = sorted([int(self.user.id), int(self.other_user_id)])
    
    is_friend = await self.check_freindship(users_id[0], users_id[1])
    
    if not is_friend:
      await self.close()
      return
    
    self.room_name = f'chat_{users_id[0]}_{users_id[1]}'
    self.room_group_name = f"group_{self.room_name}"
    await self.channel_layer.group_add(
      self.room_group_name, self.channel_name
      )
    await self.accept()
    
  async def disconnect(self, close_code):
    await self.channel_layer.group_discard(
      self.room_group_name, self.channel_name
    )
  
  async def receive(self, text_data):
    text_data_json = json.loads(text_data)
    message = text_data_json.get('message')
    
    if not message or not message.strip():
      return
    
    saved_msg = await self.save_message(self.user.id, self.other_user_id, message)
    
    project_tz = timezone.get_current_timezone()
    local_dt = saved_msg.timestamp.astimezone(project_tz)
    time = django_date(local_dt, "M d, Y, g:i a")
    
    await self.channel_layer.group_send(
      self.room_group_name, {
        "type":"chat_message",
        "message": str(message),
        "sender_id": self.user.id,
        "timestamp": time,
      }
    )
    
  async def chat_message(self, event):
    message = event.get('message')
    sender_id = event.get('sender_id')
    timestamp = event.get('timestamp')
    await self.send(text_data=json.dumps({
      "message": str(message),
      "sender_id": sender_id,
      "timestamp": timestamp,
    }))
    
  @database_sync_to_async
  def save_message(self, sender_id, receiver_id, msg):
    sender = User.objects.get(id=sender_id)
    receiver = User.objects.get(id=receiver_id)
    
    return ChatMessage.objects.create(
      sender=sender,
      receiver=receiver,
      message=str(msg),
    )
  @database_sync_to_async
  def check_freindship(self, sender_id, receiver_id):
    return Friendship.objects.filter(
      Q(sender_id=sender_id, receiver_id=receiver_id) |
      Q(sender_id=receiver_id, receiver_id=sender_id),
      relation="active"
      ).exists()