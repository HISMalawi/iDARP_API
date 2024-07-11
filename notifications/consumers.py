import json
import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from notifications.views import GetUserNotifications

logger = logging.getLogger(__name__)

class UserNotificationConsumer(AsyncJsonWebsocketConsumer):
    # WebSocket connection handler
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()

        # Adding the client to a fixed group when connected
        # self.channel_name is unique to each client
        print("Connected ", self.channel_name)
        await self.channel_layer.group_add("fixed_group", self.channel_name)

    # WebSocket disconnection handler
    async def disconnect(self, close_code):
        print("WebSocket disconnected:", close_code)
        print("Disconnected ", self.channel_name)

        # Removing the client from the fixed group when disconnected
        await self.channel_layer.group_discard("fixed_group", self.channel_name)

    # Asynchronous function to fetch user notifications from the database
    @database_sync_to_async
    def get_user_notifications(self, user_id):
        return GetUserNotifications.get_all_user_notifications(user_id)

    # Asynchronous function to fetch user active roles from the database
    @database_sync_to_async
    def get_user_active_roles(self, user_id):
        return GetUserNotifications.get_users_ids(user_id)

    # WebSocket message receiving handler
    async def receive(self, text_data=None, **kwargs):
        print("Received data:", text_data)

        # Parse received JSON data
        data = json.loads(text_data)
        user_id = data['user_id']

        # Fetch user notifications asynchronously
        user_notifications = await self.get_user_notifications(user_id)

        # Send user notifications back to the client
        await self.send(text_data=json.dumps({
            'notifications': user_notifications
        }))

    # WebSocket event handler for notification creation
    async def notification_created(self, event):
        print("send notification")

        # Send a notification event to the client
        await self.send(text_data=json.dumps({
            'type': 'notification.created',
            'notification_id': event['notification_id'],
        }))
