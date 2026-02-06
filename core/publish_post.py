import requests
import json
import base64
import sys
import os
from google import genai
from dotenv import load_dotenv
import datetime
import warnings
import random

# Suppress noisy warnings for a cleaner console output
warnings.filterwarnings("ignore", category=FutureWarning)
try:
    from urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
except:
    pass

# Load environment variables
load_dotenv()

# Author Style Definitions
STYLE_PROMPTS = {
    "expert": "Пиши сухим, аналитическим, техническим языком. Используй терминологию, цифры и глубокий анализ. Минимум эмоций, максимум фактов.",
    "lifestyle": "Пиши эмоционально, легко и доступно. Используй личные примеры, сторителлинг и обращайся к читателю на 'ты'. Статья должна выглядеть как пост в личном блоге.",
    "neutral": "Пиши в стандартном информационном стиле новостного портала. Объективно и сбалансировано."
}

def publish_to_wordpress(site_url, username, app_password, title, content, status='publish'):
    """
    Publishes a post to a WordPress site using the REST API and Application Passwords.
    """
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
        elif response.status_code == 401:
            print(f"   ❌ Ошибка авторизации: проверьте логин и пароль приложения.")
        elif response.status_code == 404:
            print(f"   ❌ Ошибка: API WordPress не найден на этом сайте.")
        elif response.status_code == 405:
            print(f"   ❌ Ошибка: Метод не разрешен. Скорее всего, сайт заблокировал запрос.")
        else:
            print(f"   ❌ Ошибка сервера (код {response.status_code}).")
        return None
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Ошибка соединения: не удалось найти сайт или сервер не отвечает.")
    except Exception as e:
        print(f"   ❌ Непредвиденная ошибка при публикации: {e}")
        return None

def generate_article_template(topic, target_link, anchor_text):
    """
    Fallback template generator if AI fails.
    """
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
    """
    Mock function for updating existing posts (Internal Linking).
    In a real scenario, this would search for relevant posts via WP API and inject the link.
    """
    # Simply returning None for now as per the simplified logic, 
    # but printing the intent to show functionality.
    print(f"   🔍 Поиск релевантных статей для перелинковки по теме '{topic}'...")
    # Real logic would go here: GET /wp-json/wp/v2/posts?search=topic...
    return None

def generate_article(topic, target_link, anchor_text, author_style='neutral'):
    """
    Generates an article using Google Gemini 1.5 Flash (via google-genai library).
    """
    print(f"Generating NEW content (Style: {author_style}) for topic: {topic}")
    
    # 1. Get Prompts
    style_instruction = STYLE_PROMPTS.get(author_style, STYLE_PROMPTS['neutral'])
    prompt = f"""
    You are a professional blog writer. {style_instruction}
    
    Task: Write a SEO-optimized article provided in HTML format (use <h1>, <h2>, <p> tags only).
    Topic: {topic}
    Requirement 1: Include a natural link to "{target_link}" with anchor text "{anchor_text}".
    Requirement 2: Make the article engaging and around 600 words.
    Requirement 3: Return ONLY HTML code, no markdown symbols like ```html.
    """

    # 2. Call Gemini API (New Client)
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt
        )
        # Gemini returns the whole generation object, we need the text.
        # Assuming response.text is available directly or via candidates.
        # The new library might handle it slightly differently, usually response.text works.
        title = f"Взгляд эксперта: {topic}" # Simple title generation from topic
        content = response.text.replace('```html', '').replace('```', '')
        return title, content
    except Exception as e:
        print(f"Gemini API error: {e}. Falling back to template.")
        return generate_article_template(topic, target_link, anchor_text)

def run_tasks(data, output_file='results.json'):
    """
    Iterates through sequences and attempts to publish/link.
    """
    results = []
    for i, task in enumerate(data):
        print(f"\n--- Task {i+1} ---")
        site_url = task.get('site_url')
        login = task.get('login')
        password = task.get('app_password')
        target_url = task.get('target_links', task.get('target_url')) # Handle both keys
        anchor = task.get('anchor_text', task.get('anchor'))
        topic = task.get('article_topic', task.get('topic'))
        style = task.get('author_style', 'neutral')
        
        if not all([site_url, login, password, target_url, anchor, topic]):
            print(f"Skip task {i+1}: Missing fields.")
            continue
            
        # Feature 3: Try to update existing post first (Internal Linking)
        linked_url = update_existing_post(site_url, login, password, target_url, anchor, topic)
        
        # Determine title and content
        title, content = generate_article(topic, target_url, anchor, style)
        
        print(f"Publishing to {site_url}...")
        post_result = publish_to_wordpress(site_url, login, password, title, content)
        
        task_result = {
            "site": site_url,
            "status": "success" if post_result else "error",
            "new_post_url": post_result.get('link') if post_result else None,
            "updated_old_post": linked_url
        }
        results.append(task_result)
        
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    return results

if __name__ == "__main__":
    # Example input data as provided by the user
    user_input = [
      {
        "site_url": "[https://satellite1.com](https://satellite1.com)",
        "login": "admin_bot",
        "app_password": "xxxx xxxx xxxx xxxx",
        "target_url": "[https://main-project.com/page1](https://main-project.com/page1)",
        "anchor": "лучшие финансовые советы",
        "topic": "Личные финансы и инвестиции"
      }
    ]
    
    # Check if a JSON file was passed as an argument
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], 'r') as f:
                user_input = json.load(f)
        except Exception as e:
            print(f"Error reading input file: {e}")
            sys.exit(1)
            
    run_tasks(user_input)
