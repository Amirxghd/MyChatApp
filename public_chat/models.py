from django.db import models

# Create your models here.
from django.db import models
from django.conf import settings
from django.urls import reverse



def get_profile_image_filepath(self, filename):

    return 'group_images/' + str(self.pk) + '/group_image.png'


def get_default_profile_image():
    return "default_images/group-default.png"


class PublicChatRoom(models.Model):

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owner', blank=True, null=True)
    title = models.CharField(max_length=255, blank=False, null=False)
    chat_username = models.CharField(max_length=255, unique=True, blank=False, null=False, default='')
    invite_link = models.CharField(max_length=255,  blank=True, null=True)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, help_text='users who are connected', blank=True)
    registered_users = models.ManyToManyField(settings.AUTH_USER_MODEL, help_text='users who are invited to the group',
                                              blank=True, related_name='registered_users')
    room_image = models.ImageField(max_length=255, upload_to=get_profile_image_filepath, null=True, blank=True,
                                      default=get_default_profile_image)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('join_group', kwargs={'invite_link': self.invite_link})

    def connect_user(self, user):
        is_user_added = False
        if user not in self.users.all():
            self.users.add(user)
            self.save()
            is_user_added = True
        elif user in self.users.all():
            is_user_added = True
        return is_user_added

    def disconnect_user(self, user):
        is_user_removed = False
        if user in self.users.all():
            self.users.remove(user)
            self.save()
            is_user_removed = True
        return is_user_removed

    @property
    def group_name(self):
        return "publicChatRoom_{}".format(self.id)


class PublicRoomChatMessageManager(models.Manager):
    def by_room(self, room):
        qs = PublicRoomChatMessage.objects.filter(room=room).order_by('-timestamp')
        return qs


class PublicRoomChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(PublicChatRoom, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)

    objects = PublicRoomChatMessageManager()

    def __str__(self):
        return self.content




