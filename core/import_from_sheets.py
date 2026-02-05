import csv
import json
import os
import sys

def csv_to_json(csv_file='sites_import.csv', json_file='sites_data.json'):
    """
    Converts a Google Sheets exported CSV into the formatted sites_data.json.
    """
    if not os.path.exists(csv_file):
        print(f"❌ Ошибка: Файл {csv_file} не найден. Сначала экспортируйте таблицу в CSV.")
        return

    sites_data = []
    try:
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic validation and cleaning
                site_entry = {
                    "site_url": row.get('Site URL', '').strip(),
                    "login": row.get('Login', '').strip(),
                    "app_password": row.get('App Password', '').strip(),
                    "target_url": row.get('Target Link', '').strip(),
                    "anchor": row.get('Anchor Text', '').strip(),
                    "topic": row.get('Article Topic', '').strip(),
                    "author_style": row.get('Author Style (expert/lifestyle/neutral)', 'neutral').strip().lower()
                }
                
                # Only add if essential fields are present
                if site_entry["site_url"] and site_entry["app_password"]:
                    sites_data.append(site_entry)

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sites_data, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Успех! {len(sites_data)} сайтов импортировано в {json_file}")
        
    except Exception as e:
        print(f"❌ Ошибка при конвертации: {e}")

if __name__ == "__main__":
    csv_file_arg = sys.argv[1] if len(sys.argv) > 1 else 'sites_import.csv'
    csv_to_json(csv_file_arg)
