import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from chat.models import ChatMessage, Friendship
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.defaultfilters import date as django_date
from django.db.models import Q
import asyncio


class ChatConsumer(AsyncWebsocketConsumer):
  
  ### CONNECT THE BROWSERS
  async def connect(self):
    self.user = self.scope['user'] # user who sent the message, or open the connection
    if not self.user.is_authenticated:
      await self.close()
      return
    
    # receiver or another user id, grab from url
    self.other_user_id = self.scope['url_route']['kwargs']['other_user_id']
    
    
    if int(self.other_user_id) == 0:
      self.room_name = f"chat_{self.user.id}_ai"
      self.room_group_name = f"group_{self.room_name}"
    else:
      # sorting the ids to match with room_name
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
  
  
  ##### DISCONNECT THE BROWSERS
  async def disconnect(self, close_code):
    await self.channel_layer.group_discard(
      self.room_group_name, self.channel_name
    )
  
  
  ### RECEIVE MESSAGE
  async def receive(self, text_data):
    text_data_json = json.loads(text_data) # text that user send
    message = text_data_json.get('message')
    
    if not message or not message.strip():
      return
    
    saved_msg = await self.save_message(sender_id=self.user.id, receiver_id=0, msg=message)
    
    time = self.get_formated_time(saved_msg.timestamp)
    
    await self.channel_layer.group_send(
      self.room_group_name, {
        "type":"chat_message",
        "message": str(message),
        "sender_id": self.user.id,
        "timestamp": time,
      }
    )

    if int(self.other_user_id) == 0:
      asyncio.create_task(self.run_ai(message))
  
  ### BORDCAST MESSAGE
  async def chat_message(self, event):
    message = event.get('message')
    sender_id = event.get('sender_id')
    timestamp = event.get('timestamp')
    await self.send(text_data=json.dumps({
      "message": str(message),
      "sender_id": sender_id,
      "timestamp": timestamp,
    }))
  
  
  ### FOR FORMATED TIME
  def get_formated_time(self, timestamp):
    project_tz = timezone.get_current_timezone()
    local_dt = timestamp.astimezone(project_tz)
    return django_date(local_dt, "M d, Y, g:i a")
    
    
    
  ### SAVE MESSAGES TO DB
  @database_sync_to_async
  def save_message(self, sender_id, receiver_id, msg):
    if int(sender_id) == 0:
      sender = User.objects.get(username="AI_Assistant")
    else:
      sender = User.objects.get(id=sender_id)
    if int(receiver_id) == 0:
      receiver = User.objects.get(username="AI_Assistant")
    else:
      receiver = User.objects.get(id=receiver_id)
    
    return ChatMessage.objects.create(
      sender=sender,
      receiver=receiver,
      message=str(msg),
    )
  
  ### CHECK FRIENDSHIP TO ALLOW THE CONNECTION OR NOT
  @database_sync_to_async
  def check_freindship(self, sender_id: int, receiver_id: int):
    if sender_id==0 or receiver_id==0:
      return True
    return Friendship.objects.filter(
      Q(sender_id=sender_id, receiver_id=receiver_id) |
      Q(sender_id=receiver_id, receiver_id=sender_id),
      relation="active"
      ).exists()
  
  
  ### FUNTION FOR AI 
  async def run_ai(self, user_message):
    '''
    Wait for 0.1 sec before running ai function.
    Give the proper time for websocket to display the user's
    message first, then only call for ai response.
    '''
    await asyncio.sleep(0.1) 
    import os
    from google import genai
    from dotenv import load_dotenv
    
    load_dotenv()
    
    API_KEY= os.environ.get('GOOGLE_API_KEY')
    client = genai.Client(api_key=API_KEY)
    
    history = await self.get_ai_history()
    
    try:
      chat = client.chats.create(model="gemini-2.5-flash", history=history)
      response =  chat.send_message(user_message)
      ai_reply = response.text
      
    except Exception as e:
      print(f"-----AI ERROR: {e}-----")
      ai_reply = "Sorry, I'm unavailable right now. Please try again later."
      
    saved_msg = await self.save_message(sender_id=0, receiver_id=self.user.id, msg=ai_reply)
    time = self.get_formated_time(saved_msg.timestamp)
    
    await self.channel_layer.group_send(
      self.room_group_name,
      {
        "type":"chat_message",
        "message": str(ai_reply),
        "sender_id": 0,
        "timestamp": time,
      }
    )
    
    
  
  #### AI HISTORY GRAB
  @database_sync_to_async
  def get_ai_history(self):
    from google.genai import types
    ai_user = User.objects.get(username="AI_Assistant")
    messages = ChatMessage.objects.filter(
      Q(sender=ai_user, receiver=self.user) |
      Q(sender=self.user.id, receiver=ai_user)
    ).order_by('timestamp')
    
    history = []
    for message in messages:
      role = "user" if message.sender==self.user else "model"
      history.append(types.Content(
        role=role,
        parts=[types.Part(text=message.message)]
      ))
    return history