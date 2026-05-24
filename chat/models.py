from django.db import models
from django.contrib.auth.models import User
from django.db.models.functions import Least, Greatest

# Create your models here.
class Friendship(models.Model):
  STATUS = (
    ('pending', 'Pending'),
    ('active', 'Active'),
  )
  sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends_sent")
  receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends_received")
  relation = models.CharField(max_length=20, choices=STATUS, default='pending')
  
  class Meta:
    constraints = [
       models.UniqueConstraint(Least('sender', 'receiver'), Greatest('sender', 'receiver'), name='unique_relation')
      ]
  
  def clean(self):
    if self.sender == self.receiver:
      raise ValidationError("You cannot friend yourself.")
  
  def __str__(self):
    return f"{self.sender.username} and {self.receiver.username}"
  

class ChatMessage(models.Model):
  sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender")
  receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="receiver")
  message = models.TextField()
  timestamp = models.DateTimeField(auto_now_add=True)
  
  class Meta:
    ordering = ['timestamp']
    
  def __str__(self):
    return f"{self.sender.username} to {self.receiver.username}: {self.message[:20]}"