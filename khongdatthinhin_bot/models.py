
from django.db import models
from django.db.models import CASCADE
from django_tgbot.models import AbstractTelegramUser, AbstractTelegramChat, AbstractTelegramState

class MenuItem(models.Model):
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Employee(models.Model):
    telegram_chat = models.OneToOneField('TelegramChat', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        # Lấy id thực tế của chat Telegram
        if self.telegram_chat and hasattr(self.telegram_chat, 'telegram_id'):
            chat_id = self.telegram_chat.telegram_id
        else:
            chat_id = self.telegram_chat_id
        return self.name or f"Employee chat_id={chat_id}"

class Order(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey('MenuItem', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)




class TelegramUser(AbstractTelegramUser):
    pass

class TelegramChat(AbstractTelegramChat):
    pass

class TelegramState(AbstractTelegramState):
    telegram_user = models.ForeignKey(TelegramUser, related_name='telegram_states', on_delete=CASCADE, blank=True, null=True)
    telegram_chat = models.ForeignKey(TelegramChat, related_name='telegram_states', on_delete=CASCADE, blank=True, null=True)

    class Meta:
        unique_together = ('telegram_user', 'telegram_chat')

