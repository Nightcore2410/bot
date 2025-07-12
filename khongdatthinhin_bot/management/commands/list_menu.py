from django.core.management.base import BaseCommand
from khongdatthinhin_bot.models import MenuItem

class Command(BaseCommand):
    help = 'Liệt kê tất cả món ăn trong MenuItem'

    def handle(self, *args, **options):
        items = MenuItem.objects.all()
        if not items:
            self.stdout.write(self.style.WARNING('Không có món ăn nào trong menu.'))
            return
        self.stdout.write(self.style.SUCCESS('Danh sách món ăn:'))
        for item in items:
            status = ' (Đang mở)' if item.is_active else ' (Đã ẩn)'
            self.stdout.write(f'- {item.name}{status}')
