from django.db import models
from django.conf import settings
from django.urls import reverse


class PrivateChatRoom(models.Model):

    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user1')
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user2')

    def __str__(self):
        return 'Private_chat Between 1-' + str(self.user1) + ' 2- ' + str(self.user2)

    @property
    def group_name(self):
        return "PrivateChat_{}".format(self.id)


class PrivateRoomChatMessageManager(models.Manager):
    def by_room(self, room):
        date_query = PrivateRoomChatMessage.objects.filter(room=room).order_by('-timestamp')
        return date_query


class PrivateRoomChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(PrivateChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)

    objects = PrivateRoomChatMessageManager()

    def __str__(self):
        return self.content
