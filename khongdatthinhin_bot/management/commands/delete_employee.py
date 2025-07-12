from django.core.management.base import BaseCommand
from khongdatthinhin_bot.models import Employee

class Command(BaseCommand):
    help = 'Hiển thị danh sách người đã đăng ký và Telegram ID.'

    def add_arguments(self, parser):
        parser.add_argument('telegram_id', nargs='?', type=str, help='Telegram ID của nhân viên cần xóa')
        parser.add_argument('--all', action='store_true', help='Xóa tất cả nhân viên')

    def handle(self, *args, **options):
        telegram_id = options.get('telegram_id')
        if options.get('all'):
            count = Employee.objects.count()
            Employee.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Đã xóa toàn bộ {count} nhân viên.'))
            return
        if telegram_id:
            qs = Employee.objects.filter(telegram_chat__telegram_id=telegram_id)
            count = qs.count()
            if count == 0:
                self.stdout.write(self.style.WARNING(f'Không tìm thấy nhân viên với Telegram ID: {telegram_id}'))
                return
            qs.delete()
            self.stdout.write(self.style.SUCCESS(f'Đã xóa {count} nhân viên với Telegram ID: {telegram_id}'))
            return
        employees = Employee.objects.select_related('telegram_chat').all()
        if not employees:
            self.stdout.write('Chưa có ai đăng ký.')
            return
        self.stdout.write('Danh sách người đã đăng ký:')
        for emp in employees:
            name = emp.name or '(chưa có tên)'
            tele_id = emp.telegram_chat.telegram_id if emp.telegram_chat else '(không có ID)'
            self.stdout.write(f'- {name} | Telegram ID: {tele_id}')
