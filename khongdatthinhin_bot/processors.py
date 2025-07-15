# Đảm bảo import đầy đủ các module cần thiết cho các decorator và biến sử dụng phía dưới
from django_tgbot.decorators import processor
from django_tgbot.state_manager import state_types
from .bot import state_manager
from .models import Employee, TelegramChat, MenuItem, Order, OrderItem, TelegramState
from django.utils import timezone
from django.db.models import Sum
import pytz
from datetime import datetime
# --- /+ ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_plus_order(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/+":
        return
    chat_id = chat.get_id()
    # Gửi menu hiện tại nếu có
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_text = f.read().strip()
        if menu_text:
            bot.sendMessage(chat_id, f"Menu hôm nay:\n{menu_text}\n\nTrả lời số thứ tự món bạn muốn đặt thêm.")
    except Exception:
        bot.sendMessage(chat_id, "Không tìm thấy menu. Vui lòng liên hệ admin để cập nhật menu.")
        return
    state.set_name("THEM_MON_PLUS")
    state.save()

# --- Nhận số thứ tự món từ user để thêm món mới vào order (không xoá món cũ, cho lệnh /+) ---
@processor(state_manager, from_states=["THEM_MON_PLUS"], update_types=['message'])
def save_plus_mon(bot, update, state):
    chat = update.get_chat()
    if chat.get_type() != 'private':
        return
    chat_id = chat.get_id()
    text = update.get_message().get_text().strip()
    # Kiểm tra số thứ tự
    try:
        idx = int(text) - 1
    except ValueError:
        bot.sendMessage(chat_id, "Vui lòng nhập số thứ tự món muốn đặt thêm.")
        return
    # Đọc menu hiện tại
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception:
        bot.sendMessage(chat_id, "Không tìm thấy menu. Vui lòng liên hệ admin để cập nhật menu.")
        state.set_name("")
        state.save()
        return
    if idx < 0 or idx >= len(menu_lines):
        bot.sendMessage(chat_id, f"Số thứ tự không hợp lệ. Chọn số từ 1 đến {len(menu_lines)}.")
        return
    menu_name = menu_lines[idx].split('. ', 1)[-1] if '. ' in menu_lines[idx] else menu_lines[idx]
    db_chat, _ = TelegramChat.objects.get_or_create(telegram_id=chat_id)
    try:
        employee = Employee.objects.get(telegram_chat=db_chat)
    except Employee.DoesNotExist:
        bot.sendMessage(chat_id, "Bạn chưa đăng ký tên. Vui lòng gửi /start và nhập tên trước khi đặt món.")
        return
    today = timezone.now().date()
    order, _ = Order.objects.get_or_create(employee=employee, created_at__date=today)
    # Nếu không tìm thấy món trong DB, tự động thêm vào DB và đánh dấu is_active=True
    menu_item = MenuItem.objects.filter(name=menu_name, is_active=True).first()
    if not menu_item:
        menu_item, created = MenuItem.objects.get_or_create(name=menu_name)
        menu_item.is_active = True
        menu_item.save()
    # Nếu đã có OrderItem cho món này thì tăng số lượng, chưa có thì tạo mới
    order_item, created = OrderItem.objects.get_or_create(order=order, menu_item=menu_item, defaults={'quantity': 1})
    if not created:
        order_item.quantity += 1
        order_item.save()
    bot.sendMessage(chat_id, f"Đã thêm món: {menu_name} vào đơn. Nếu muốn thêm nữa, hãy gửi /+ tiếp.")
    state.set_name("")
    state.save()
# --- /them ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_them_order(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/them":
        return
    chat_id = chat.get_id()
    # Gửi menu hiện tại nếu có
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_text = f.read().strip()
        if menu_text:
            bot.sendMessage(chat_id, f"Menu hôm nay:\n{menu_text}\n\nTrả lời số thứ tự món bạn muốn đặt thêm.")
    except Exception:
        bot.sendMessage(chat_id, "Không tìm thấy menu. Vui lòng liên hệ admin để cập nhật menu.")
        return
    state.set_name("THEM_MON")
    state.save()

# --- Nhận số thứ tự món từ user để thêm món mới vào order (không xoá món cũ) ---
@processor(state_manager, from_states=["THEM_MON"], update_types=['message'])
def save_them_mon(bot, update, state):
    chat = update.get_chat()
    if chat.get_type() != 'private':
        return
    chat_id = chat.get_id()
    text = update.get_message().get_text().strip()
    # Kiểm tra số thứ tự
    try:
        idx = int(text) - 1
    except ValueError:
        bot.sendMessage(chat_id, "Vui lòng nhập số thứ tự món muốn đặt thêm.")
        return
    # Đọc menu hiện tại
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception:
        bot.sendMessage(chat_id, "Không tìm thấy menu. Vui lòng liên hệ admin để cập nhật menu.")
        state.set_name("")
        state.save()
        return
    if idx < 0 or idx >= len(menu_lines):
        bot.sendMessage(chat_id, f"Số thứ tự không hợp lệ. Chọn số từ 1 đến {len(menu_lines)}.")
        return
    menu_name = menu_lines[idx].split('. ', 1)[-1] if '. ' in menu_lines[idx] else menu_lines[idx]
    db_chat, _ = TelegramChat.objects.get_or_create(telegram_id=chat_id)
    try:
        employee = Employee.objects.get(telegram_chat=db_chat)
    except Employee.DoesNotExist:
        bot.sendMessage(chat_id, "Bạn chưa đăng ký tên. Vui lòng gửi /start và nhập tên trước khi đặt món.")
        return
    today = timezone.now().date()
    order, _ = Order.objects.get_or_create(employee=employee, created_at__date=today)
    # Nếu không tìm thấy món trong DB, tự động thêm vào DB và đánh dấu is_active=True
    menu_item = MenuItem.objects.filter(name=menu_name, is_active=True).first()
    if not menu_item:
        menu_item, created = MenuItem.objects.get_or_create(name=menu_name)
        menu_item.is_active = True
        menu_item.save()
    # Nếu đã có OrderItem cho món này thì tăng số lượng, chưa có thì tạo mới
    order_item, created = OrderItem.objects.get_or_create(order=order, menu_item=menu_item, defaults={'quantity': 1})
    if not created:
        order_item.quantity += 1
        order_item.save()
    bot.sendMessage(chat_id, f"Đã thêm món: {menu_name} vào đơn. Nếu muốn thêm nữa, hãy gửi /them tiếp.")
    state.set_name("")
    state.save()
from django_tgbot.decorators import processor
from django_tgbot.state_manager import state_types
from .bot import state_manager
from .models import Employee, TelegramChat, MenuItem, Order, OrderItem, TelegramState
from django.utils import timezone
from django.db.models import Sum
import pytz
from datetime import datetime

# --- /update ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_updateorder(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/up":
        return
    chat_id = chat.get_id()
    bot.sendMessage(chat_id, "Hãy gửi danh sách món ăn mới, mỗi món một dòng. Danh sách cũ sẽ bị thay thế.")
    state.set_name("ASK_UPDATE_MENU")
    state.save()

# --- Nhận danh sách món mới, cập nhật menu và gửi cho tất cả user đã đăng ký ---
@processor(state_manager, from_states=["ASK_UPDATE_MENU"], update_types=['message'])
def save_update_menu(bot, update, state):
    chat_id = update.get_chat().get_id()
    menu_text = update.get_message().get_text().strip()
    items = [line.strip() for line in menu_text.splitlines() if line.strip()]
    if not items:
        bot.sendMessage(chat_id, "Không có món nào được cập nhật.")
        state.set_name("")
        state.save()
        return
    MenuItem.objects.all().update(is_active=False)
    for name in items:
        obj, _ = MenuItem.objects.get_or_create(name=name)
        obj.is_active = True
        obj.save()
    menu_numbered = "\n".join(f"{i+1}. {n}" for i, n in enumerate(items))
    # Xoá tất cả order và orderitem kể từ thời điểm cập nhật menu mới
    # (xoá mọi order có created_at >= thời điểm cập nhật menu này)
    menu_update_time = timezone.now()
    all_orders = Order.objects.filter(created_at__gte=menu_update_time)
    OrderItem.objects.filter(order__in=all_orders).delete()
    all_orders.delete()
    # Lưu menu mới nhất
    try:
        with open('current_menu.txt', 'w', encoding='utf-8') as f:
            f.write(menu_numbered)
        # Lưu thời điểm cập nhật menu
        with open('menu_last_updated.txt', 'w', encoding='utf-8') as f2:
            f2.write(str(menu_update_time.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))))
    except Exception as e:
        bot.sendMessage(chat_id, f"Lỗi khi lưu menu: {e}")
    # Gửi menu mới cho tất cả user đã đăng ký
    for emp in Employee.objects.select_related('telegram_chat').all():
        if emp.name and emp.telegram_chat and emp.telegram_chat.telegram_id:
            try:
                bot.sendMessage(emp.telegram_chat.telegram_id, f"Menu hôm nay đã được cập nhật!\n{menu_numbered}\n\nĐã cập nhật menu")
            except Exception:
                pass
    # Gửi lại menu cho người gửi (admin hoặc ai vừa cập nhật)
    bot.sendMessage(chat_id, f"Menu hôm nay:\n{menu_numbered}\n\nMenu hôm nay đã được cập nhật!.")
    state.set_name("")
    state.save()

# --- /start ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_start(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/start":
        return
    # Chỉ xử lý nếu là chat cá nhân (private)
    if chat.get_type() != 'private':
        return
    chat_id = chat.get_id()
    db_chat, _ = TelegramChat.objects.get_or_create(telegram_id=chat_id)
    employee, created = Employee.objects.get_or_create(telegram_chat=db_chat)
    if created or not employee.name:
        bot.sendMessage(chat_id, "Chào bạn! Vui lòng cho tôi biết tên của bạn.")
        state.set_name("ASK_NAME")
        state.save()
    else:
        bot.sendMessage(chat_id, f"Xin chào {employee.name}!")
        # Gửi menu hiện tại nếu có
        try:
            with open('current_menu.txt', 'r', encoding='utf-8') as f:
                menu_text = f.read().strip()
            if menu_text:
                bot.sendMessage(chat_id, f"Menu hôm nay:\n{menu_text}\n\nVui lòng trả lời số thứ tự món bạn muốn đặt.")
        except Exception:
            pass

# --- Lưu tên ---
@processor(state_manager, from_states=['ASK_NAME'], update_types=['message'])
def save_name(bot, update, state):
    chat = update.get_chat()
    if chat.get_type() != 'private':
        return
    chat_id = chat.get_id()
    name = update.get_message().get_text().strip()
    db_chat = TelegramChat.objects.get(telegram_id=chat_id)
    employee = Employee.objects.get(telegram_chat=db_chat)
    employee.name = name
    employee.save()
    bot.sendMessage(chat_id, f"Cảm ơn bạn, {name}! Bạn đã đăng ký thành công.")
    # Gửi menu hiện tại nếu có
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_text = f.read().strip()
        if menu_text:
            bot.sendMessage(chat_id, f"Menu hôm nay:\n{menu_text}\n\nVui lòng trả lời số thứ tự món bạn muốn đặt.")
    except Exception:
        pass
    state.set_name("")
    state.save()



# --- /thongbao ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_thongbao(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/thongbao":
        return
    chat_id = chat.get_id()
    # Chỉ cho phép admin gửi lệnh này
    admin_ids = [8057576507]  # <-- Thay các số này bằng chat_id admin thực tế của bạn
    if int(chat_id) not in [int(i) for i in admin_ids]:
        bot.sendMessage(chat_id, "Bạn không có quyền gửi thông báo.")
        return
    # Lấy danh sách user chưa đặt cơm hôm nay
    today = timezone.now().date()
    # Lấy tất cả Employee đã đăng ký
    all_emps = Employee.objects.select_related('telegram_chat').all()
    # Lấy id các employee đã có order hôm nay
    ordered_emp_ids = set(Order.objects.filter(created_at__date=today).values_list('employee_id', flat=True))
    count = 0
    for emp in all_emps:
        if emp.id not in ordered_emp_ids and emp.telegram_chat and emp.telegram_chat.telegram_id:
            try:
                bot.sendMessage(emp.telegram_chat.telegram_id, "Bạn chưa đặt cơm hôm nay! Vui lòng đặt món ")
                count += 1
            except Exception:
                pass
    bot.sendMessage(chat_id, f"Đã gửi nhắc nhở tới {count} user chưa đặt cơm hôm nay.")



# --- Nhận số thứ tự món từ user, lưu order, cảnh báo nếu sai ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def collect_order_item(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if chat.get_type() != 'private':
        return
    if message is None or message.get_text() is None:
        return
    text = message.get_text().strip()
    # Bỏ qua các lệnh đặc biệt
    if text.startswith("/"):
        return
    chat_id = chat.get_id()
    # Kiểm tra giờ Việt Nam, chỉ khoá nếu đã quá 9h30 và menu đã được cập nhật trước 9h30 hôm nay
    now_vn = timezone.now().astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
    menu_last_updated = None
    try:
        with open('menu_last_updated.txt', 'r', encoding='utf-8') as f:
            menu_last_updated = datetime.fromisoformat(f.read().strip())
    except Exception:
        pass
    # Nếu đã quá 9h30 và menu đã được cập nhật trước 9h30 hôm nay thì khoá đặt món
    lock_time = now_vn.replace(hour=10, minute=00, second=0, microsecond=0)
    if now_vn > lock_time:
        if menu_last_updated is not None:
            # Nếu menu cập nhật trước 9h30 hôm nay thì khoá, còn nếu sau thì mở cho tới 9h30 hôm sau
            if menu_last_updated < lock_time:
                bot.sendMessage(chat_id, "Đã hết giờ đặt món (sau 9h30 sáng). Hẹn bạn ngày mai!")
                return
    # Đọc menu hiện tại
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception:
        bot.sendMessage(chat_id, "Không tìm thấy menu. Vui lòng liên hệ admin để cập nhật menu.")
        return
    # Kiểm tra số thứ tự
    try:
        idx = int(text) - 1
    except ValueError:
        return  # Không phải số, bỏ qua
    if idx < 0 or idx >= len(menu_lines):
        bot.sendMessage(chat_id, f"Không ăn thì nhịn Dừng làm như thế. chọn số từ 1 đến {len(menu_lines)} đi .\nMenu hôm nay:\n" + "\n".join(menu_lines))
        return
    # Lấy tên món
    menu_name = menu_lines[idx].split('. ', 1)[-1] if '. ' in menu_lines[idx] else menu_lines[idx]
    # Kiểm tra đăng ký tên và id telegram
    db_chat, _ = TelegramChat.objects.get_or_create(telegram_id=chat_id)
    try:
        employee = Employee.objects.get(telegram_chat=db_chat)
    except Employee.DoesNotExist:
        bot.sendMessage(chat_id, "Bạn chưa đăng ký tên. Vui lòng gửi /start và nhập tên trước khi đặt món.")
        return
    if not employee.name or not db_chat.telegram_id:
        bot.sendMessage(chat_id, "Bạn chưa đăng ký đầy đủ tên và ID Telegram. Vui lòng gửi /start và nhập tên trước khi đặt món.")
        return
    today = timezone.now().date()
    order, _ = Order.objects.get_or_create(employee=employee, created_at__date=today)
    # Nếu không tìm thấy món trong DB, tự động thêm vào DB và đánh dấu is_active=True
    menu_item = MenuItem.objects.filter(name=menu_name, is_active=True).first()
    if not menu_item:
        # Thêm món mới vào DB nếu chưa có
        menu_item, created = MenuItem.objects.get_or_create(name=menu_name)
        menu_item.is_active = True
        menu_item.save()
    # Đảm bảo mỗi order chỉ có 1 OrderItem duy nhất (xóa tất cả OrderItem cũ của order này)
    OrderItem.objects.filter(order=order).delete()
    # Tạo OrderItem mới (chỉ 1 món cho mỗi order)
    order_item = OrderItem.objects.create(order=order, menu_item=menu_item, quantity=1)
    bot.sendMessage(chat_id, f"Bạn đã đặt món: \n- {menu_name} \n\nChọn lại số nếu muốn đặt lại món.\nKhông thể chọn lại sau 9h")

# --- /ds ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_list_orders(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/ds":
        return
    chat_id = chat.get_id()
    # Đọc menu hiện tại
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception:
        menu_lines = []
    # Lấy tên các món trong menu hiện tại
    menu_names = [line.split('. ', 1)[-1] if '. ' in line else line for line in menu_lines]
    # Lấy tất cả OrderItem có menu_item nằm trong menu hiện tại (bỏ lọc theo ngày)
    order_items = OrderItem.objects.filter(menu_item__name__in=menu_names).select_related('order__employee', 'menu_item')
    if not order_items:
        bot.sendMessage(chat_id, f"Chưa có ai đặt món hôm nay")
        return
    # Tạo dict: user -> món đã đặt
    user_orders = {}
    for oi in order_items:
        employee = oi.order.employee
        employee_name = employee.name or f"ID {employee.id}"
        if employee_name not in user_orders:
            user_orders[employee_name] = []
        if oi.menu_item and oi.menu_item.name not in user_orders[employee_name]:
            user_orders[employee_name].append(oi.menu_item.name)
    # Tạo danh sách hiển thị
    lines = []
    for user, items in user_orders.items():
        if items:
            user_line = f"{user}: " + ", ".join(items)
            lines.append(user_line)
    if lines:
        bot.sendMessage(chat_id, f"Danh sách người đặt món hôm nay:\n" + "\n".join(lines))
    else:
        bot.sendMessage(chat_id, f"Chưa có ai đặt món hôm nay")


# --- /delete ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_delete_self(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/delete":
        return
    chat_id = chat.get_id()
    try:
        db_chat = TelegramChat.objects.get(telegram_id=chat_id)
        employee = Employee.objects.get(telegram_chat=db_chat)
    except (TelegramChat.DoesNotExist, Employee.DoesNotExist):
        bot.sendMessage(chat_id, "Bạn chưa đăng ký tài khoản hoặc đã xoá trước đó.")
        return
    # Xoá tất cả order và orderitem của user này
    orders = Order.objects.filter(employee=employee)
    OrderItem.objects.filter(order__in=orders).delete()
    orders.delete()
    # Xoá employee và telegramchat
    employee.delete()
    db_chat.delete()
    bot.sendMessage(chat_id, "Tài khoản và tất cả đơn hàng của bạn đã được xoá vĩnh viễn. Nếu muốn dùng lại, hãy /start để đăng ký lại.")

# --- /dsm ---
@processor(state_manager, from_states=state_types.All, update_types=['message'])
def handle_menu_stats(bot, update, state):
    message = update.get_message()
    chat = update.get_chat()
    if message is None or message.get_text() is None or message.get_text().strip() != "/dsm":
        return
    chat_id = chat.get_id()
    # Đọc menu hiện tại
    try:
        with open('current_menu.txt', 'r', encoding='utf-8') as f:
            menu_lines = [line.strip() for line in f.readlines() if line.strip()]
    except Exception:
        menu_lines = []
    menu_names = [line.split('. ', 1)[-1] if '. ' in line else line for line in menu_lines]
    # Đếm số lượng từng món trong menu hiện tại
    item_counts = {name: 0 for name in menu_names}
    order_items = OrderItem.objects.filter(menu_item__name__in=menu_names).select_related('menu_item')
    total = 0
    for oi in order_items:
        if oi.menu_item and oi.menu_item.name in item_counts:
            item_counts[oi.menu_item.name] += oi.quantity
            total += oi.quantity
    # Chỉ hiển thị món có số lượng > 0
    lines = [f"{name}: {item_counts[name]}" for name in menu_names if item_counts[name] > 0]
    if lines:
        bot.sendMessage(chat_id, f"Số lượng từng món đã đặt:\n" + "\n".join(lines) + f"\n\nTổng số xuất ăn: {total}")
    else:
        bot.sendMessage(chat_id, f"Chưa có món nào được đặt.")

