import pandas as pd
from khongdatthinhin_bot.models import Employee

# Lấy dữ liệu Employee
rows = []
for emp in Employee.objects.all():
    rows.append({
        'ID': emp.id,
        'Name': emp.name,
        'Telegram Chat ID': emp.telegram_chat_id,
        'Telegram ID': emp.telegram_chat.telegram_id if emp.telegram_chat else '',
    })

# Xuất ra file Excel
if rows:
    df = pd.DataFrame(rows)
    df.to_excel('employee_export.xlsx', index=False)
    print('Đã xuất file employee_export.xlsx')
else:
    print('Không có dữ liệu Employee để xuất.')
