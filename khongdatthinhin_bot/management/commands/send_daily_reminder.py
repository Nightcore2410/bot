from django.core.management.base import BaseCommand
from khongdatthinhin_bot.processors import send_daily_reminder
from khongdatthinhin_bot.bot import bot

class Command(BaseCommand):
    help = 'Gửi nhắc nhở đặt món ăn sáng tới tất cả user vào 9:05 sáng mỗi ngày (giờ Việt Nam)'

    def handle(self, *args, **options):
        send_daily_reminder(bot)
        self.stdout.write(self.style.SUCCESS('Đã gửi nhắc nhở đặt món ăn sáng tới tất cả user!'))
