import requests
import json
import base64
import sys
import os
from google import genai
from dotenv import load_dotenv
import datetime
import warnings
# Google Sheets Imports
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Suppress noisy warnings
warnings.filterwarnings("ignore", category=FutureWarning)
try:
    from urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
except:
    pass

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
SHEET_ID = "1CJjN_mSwrGwp2tVuaLK0vENb2c5VnYPQw0JM43HTE-c" # ID вашей таблицы
SHEET_TAB_NAME = "Report" # Имя вкладки для отчетов

STYLE_PROMPTS = {
    "expert": "Пиши сухим, аналитическим, техническим языком. Используй терминологию, цифры и глубокий анализ. Минимум эмоций, максимум фактов.",
    "lifestyle": "Пиши эмоционально, легко и доступно. Используй личные примеры, сторителлинг и обращайся к читателю на 'ты'. Статья должна выглядеть как пост в личном блоге.",
    "neutral": "Пиши в стандартном информационном стиле новостного портала. Объективно и сбалансировано."
}

# --- HELPER FUNCTIONS ---

def log_to_google_sheet(site_url, topic, status, link, model_used):
    """
    Logs the execution result to Google Sheets using credentials from env.
    """
    try:
        json_creds = os.getenv("GOOGLE_CREDENTIALS")
        if not json_creds:
            print("⚠️ GOOGLE_CREDENTIALS missing. Skipping sheet log.")
            return

        # Parse JSON credentials
        creds_dict = json.loads(json_creds)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Open Sheet
        try:
            sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_TAB_NAME)
        except gspread.exceptions.WorksheetNotFound:
            print(f"⚠️ Worksheet '{SHEET_TAB_NAME}' not found. Using first sheet.")
            sheet = client.open_by_key(SHEET_ID).sheet1
        except Exception as e:
            print(f"⚠️ Error opening sheet: {e}")
            return

        # Prepare Row
        row = [
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            site_url,
            topic,
            link if link else "N/A",
            "✅ Success" if status == "success" else "❌ Error",
            model_used
        ]
        
        # Append
        sheet.append_row(row)
        print(f"📊 Logged to Google Sheet: {row}")

    except Exception as e:
        print(f"⚠️ Critical error logging to sheet: {e}")

def publish_to_wordpress(site_url, username, app_password, title, content, status='publish'):
    auth_string = f"{username}:{app_password}"
    auth_header = base64.b64encode(auth_string.encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/json',
        'User-Agent': 'WordPress-Publisher-Bot/1.0'
    }
    endpoint = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    payload = {'title': title, 'content': content, 'status': status}
    
    try:
        print(f"   🚀 Отправка статьи в WordPress...")
        response = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        if response.status_code == 201:
            return response.json()
        print(f"   ❌ Ошибка WordPress: {response.status_code}")
        return None
    except Exception as e:
        print(f"   ❌ Ошибка публикации: {e}")
        return None

def generate_article_template(topic, target_link, anchor_text):
    title = f"{topic}: Полный обзор и советы"
    content = f"""
    <h1>Важность темы: {topic}</h1>
    <p>В современном мире {topic} играет ключевую роль. Многие эксперты согласны с тем, что подход к этому вопросу должен быть системным.</p>
    <h2>Основные аспекты</h2>
    <p>Рассматривая <a href="{target_link}">{anchor_text}</a>, важно понимать контекст. Эффективные стратегии всегда включают анализ рисков.</p>
    <p>Мы рекомендуем детально изучить все доступные материалы.</p>
    """
    return title, content

def update_existing_post(site_url, username, app_password, target_url, anchor, topic):
    print(f"   🔍 Поиск релевантных статей для перелинковки по теме '{topic}'...")
    return None

def generate_article(topic, target_link, anchor_text, author_style='neutral'):
    print(f"Generating NEW content (Style: {author_style}) for topic: {topic}")
    style_instruction = STYLE_PROMPTS.get(author_style, STYLE_PROMPTS['neutral'])
    prompt = f"""
    You are a professional blog writer. {style_instruction}
    Task: Write a SEO-optimized article provided in HTML format (use <h1>, <h2>, <p> tags only).
    Topic: {topic}
    Requirement 1: Include a natural link to "{target_link}" with anchor text "{anchor_text}".
    Requirement 2: Make the article engaging and around 600 words.
    Requirement 3: Return ONLY HTML code, no markdown symbols like ```html.
    """
    
    model_name = "gemini-2.0-flash"
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        title = f"Взгляд эксперта: {topic}"
        if response.text:
            content = response.text.replace('```html', '').replace('```', '')
            return title, content, model_name
        else:
            raise ValueError("Empty response from AI")
            
    except Exception as e:
        print(f"⚠️ Gemini API error: {e}. Falling back to template.")
        t, c = generate_article_template(topic, target_link, anchor_text)
        return t, c, "Template (Fallback)"

# --- MAIN LOOP ---

def run_tasks(data, output_file='results.json'):
    results = []
    for i, task in enumerate(data):
        print(f"\n--- Task {i+1} ---")
        site_url = task.get('site_url')
        login = task.get('login')
        password = task.get('app_password')
        target_url = task.get('target_links', task.get('target_url')) 
        anchor = task.get('anchor_text', task.get('anchor'))
        topic = task.get('article_topic', task.get('topic'))
        style = task.get('author_style', 'neutral')
        
        if not all([site_url, login, password, target_url, anchor, topic]):
            print(f"Skip task {i+1}: Missing fields.")
            continue
            
        update_existing_post(site_url, login, password, target_url, anchor, topic)
        
        # Generator now returns model name too
        title, content, model_used = generate_article(topic, target_url, anchor, style)
        
        print(f"Publishing to {site_url}...")
        post_result = publish_to_wordpress(site_url, login, password, title, content)
        
        status = "success" if post_result else "error"
        link = post_result.get('link') if post_result else None
        
        # LOG TO GOOGLE SHEETS
        log_to_google_sheet(site_url, topic, status, link, model_used)
        
        task_result = {
            "site": site_url,
            "status": status,
            "new_post_url": link
        }
        results.append(task_result)
        
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    return results

if __name__ == "__main__":
    user_input = []
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r') as f:
                user_input = json.load(f)
        except Exception as e:
            print(f"Error reading input file: {e}")
            sys.exit(1)
            
    if not user_input:
        print("No tasks to run.")
    else:
        run_tasks(user_input)
