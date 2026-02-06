import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

# Настройки доступа (читаем JSON-ключ из переменной окружения Render)
# На Render мы создадим переменную GOOGLE_CREDENTIALS и вставим туда содержимое JSON-файла целиком.

def log_to_sheet(site_url, topic, status, link, model_used):
    try:
        # Получаем JSON-ключ из переменной окружения
        json_creds = os.getenv("GOOGLE_CREDENTIALS")
        if not json_creds:
            print("⚠️ GOOGLE_CREDENTIALS not found. Skipping sheet logging.")
            return

        creds_dict = json.loads(json_creds)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Открываем таблицу по ID (берем из ссылки)
        # Ссылка: https://docs.google.com/spreadsheets/d/1CJjN_mSwrGwp2tVuaLK0vENb2c5VnYPQw0JM43HTE-c/...
        sheet_id = "1CJjN_mSwrGwp2tVuaLK0vENb2c5VnYPQw0JM43HTE-c" 
        
        # Открываем лист 'Report'
        try:
            sheet = client.open_by_key(sheet_id).worksheet("Report")
        except:
            # Если листа нет, открываем первый
            sheet = client.open_by_key(sheet_id).sheet1

        # Формируем строку
        row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            site_url,
            topic,
            link if link else "N/A",
            "✅ Success" if status == "success" else "❌ Error",
            model_used
        ]
        
        # Добавляем строку
        sheet.append_row(row)
        print(f"📊 Logged to Google Sheet: {row}")

    except Exception as e:
        print(f"⚠️ Failed to log to Google Sheet: {e}")
