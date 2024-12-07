from chat_app.models import Thread,ChatMessage
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist



class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            await self.close()
            return

        self.chat_room = f'user_chat_room_{user.id}'
        await self.channel_layer.group_add(self.chat_room, self.channel_name)
        await self.accept()
        print(f"User {user.id} connected to {self.chat_room}")

    async def disconnect(self, close_code):
        user = self.scope['user']
        await self.channel_layer.group_discard(self.chat_room, self.channel_name)
        print(f"User {user.id} disconnected from {self.chat_room}, Close code: {close_code}")

        
    async def receive(self, text_data):
        try:
            receive_data = json.loads(text_data)
            msg = receive_data.get('message')
            sent_by_id = receive_data.get('sent_by')
            sent_to_id = receive_data.get('sent_to')
            thread_id = receive_data.get('thread_id')

            print(f"Received message from {sent_by_id} to {sent_to_id}: {msg}")

            if not msg:
                print("Error: Empty message")
                return

            sent_by_user = await self.get_user_object(sent_by_id)
            sent_to_user = await self.get_user_object(sent_to_id)
            thread_obj = await self.get_thread(thread_id)

            if not sent_by_user or not sent_to_user:
                print("Error: Invalid sender or receiver")
                return
            if not thread_obj:
                print("Error: Invalid thread")
                return

            await self.create_chat_message(thread_obj, sent_by_user, msg)

            response = {
                'message': msg,
                'sent_by': sent_by_id,
                'thread_id': thread_id
            }

            # Send message to the recipient
            other_user_chat_room = f'user_chat_room_{sent_to_id}'
            await self.channel_layer.group_send(other_user_chat_room, {
                'type': 'chat_message',
                'text': json.dumps(response)
            })

            # Send message to self
            await self.channel_layer.group_send(self.chat_room, {
                'type': 'chat_message',
                'text': json.dumps(response)
            })

        except Exception as e:
            print(f"Error in receive: {e}")
            await self.close()


    async def chat_message(self, event):
            await self.send(text_data=event['text'])

    @database_sync_to_async  
    def get_user_object(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None

    @database_sync_to_async  
    def get_thread(self, thread_id):
        try:
            return Thread.objects.get(id=thread_id)
        except Thread.DoesNotExist:
            print(f"Thread {thread_id} does not exist.")
            return None


        
    @database_sync_to_async  
    def create_chat_message(self, thread, user, msg):
        if thread and user:
            return ChatMessage.objects.create(thread=thread, user=user, message=msg)
        return None
