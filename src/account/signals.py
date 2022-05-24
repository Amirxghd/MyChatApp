from account.models import Account
from public_chat.models import PublicChatRoom
from django.db.models.signals import post_save

def add_to_general_group(sender, instance, **kwargs):
    try:
        group = PublicChatRoom.objects.get(chat_username__iexact='general')
    except PublicChatRoom.DoesNotExist:
        group = PublicChatRoom.objects.create(chat_username='General', title='General')
        group.save()
    group.registered_users.add(instance)


post_save.connect(add_to_general_group, sender=Account)