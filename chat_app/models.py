import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
# Create your models here.

User =  get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='chat_images/', blank=True, null=True)

    def __str__(self):
        return self.user.username
    
class ThreadManager(models.Manager):
    def by_user(self, **kwargs):
        user = kwargs.get('user')
        print(f"User being queried: {user.username}")  # Debugging line
        lookup = Q(first_person=user) | Q(second_person=user)
        qs = self.get_queryset().filter(lookup).distinct()
        print(f"Result Count: {qs.count()}")  # Debugging line
        return qs




class Thread(models.Model):
    first_person = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True,related_name='thread_first_person')
    second_person = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True,related_name='thread_second_person')
    
    updated =  models.DateTimeField(auto_created=True)
    timestamp = models.DateTimeField(auto_created=True)
    
    
    
    objects = ThreadManager() 
    class Meta:
        unique_together = ['first_person','second_person']
        
class ChatMessage(models.Model):
    thread = models.ForeignKey(Thread,null=True,blank=True,on_delete=models.CASCADE,related_name='chat_message_thread')
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False) 
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:20]}"
    
class PasswordReset(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    reset_id = models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    created_when = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Password reset for {self.user.username} at {self.created_when}"
    





    
   