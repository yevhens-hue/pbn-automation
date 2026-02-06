import requests
import json
import base64
import sys
import os
import google.generativeai as genai
from dotenv import load_dotenv
import datetime
import warnings

# Suppress noisy warnings for a cleaner console output
warnings.filterwarnings("ignore", category=FutureWarning)
try:
    from urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
except:
    pass

# Load environment variables
load_dotenv()

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "ТВОЙ_API_KEY")
if GEMINI_API_KEY != "ТВОЙ_API_KEY":
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

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

def get_random_image_url(topic):
    """
    Returns a URL for a random image based on the topic using Unsplash Source.
    """
    # Using Unsplash Source (redirection service)
    safe_topic = requests.utils.quote(topic)
    return f"https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?auto=format&fit=crop&q=80&w=1200" # fallback to a finance default
    # Actually, a better dynamic way:
    # return f"https://loremflickr.com/1200/800/{safe_topic}" 

def log_generation(topic, style, prompt, response):
    """
    Logs Gemini prompt and response for future analysis.
    """
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "topic": topic,
        "style": style,
        "prompt": prompt,
        "response": response
    }
    with open("generation_logs.jsonl", "a") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def generate_article(topic, anchor, target_url, style="neutral"):
    """
    Generates article content using Gemini API with dynamic persona and logging.
    """
    persona = STYLE_PROMPTS.get(style, STYLE_PROMPTS["neutral"])
    image_url = f"https://loremflickr.com/1200/800/{requests.utils.quote(topic)}"
    
    if model:
        print(f"Using Gemini API ({style} style) to generate content for: {topic}")
        prompt = f"""
        Ты — автор контента со следующим стилем: {persona}
        
        Напиши уникальную полезную статью на тему: {topic}.
        Требования:
        1. Объем около 2500 знаков.
        2. Используй заголовок H1 и несколько подзаголовков H2.
        3. Органично и нативно вставь в текст ссылку <a href="{target_url}">{anchor}</a>. 
           Ссылка должна быть частью предложения и не выглядеть как реклама.
        4. Формат вывода: HTML (только содержимое тега body, без <html> или <body>).
        
        В начале статьи ПЕРЕД текстом вставь изображение: <img src="{image_url}" alt="{topic}" style="width:100%; height:auto; margin-bottom:20px;">
        """
        try:
            response = model.generate_content(prompt)
            full_text = response.text
            
            # Log the generation
            log_generation(topic, style, prompt, full_text)
            
            if "<h1>" in full_text:
                title_start = full_text.find("<h1>") + 4
                title_end = full_text.find("</h1>")
                title = full_text[title_start:title_end].strip()
                content = full_text[title_end+5:].strip()
            else:
                title = f"{topic}: Полное руководство"
                content = full_text
                
            return title, content
        except Exception as e:
            print(f"Gemini API error: {e}. Falling back to template.")

    # Fallback remains similar
    title = f"{topic}: {style.capitalize()} взгляд на проблему"
    content = f'<img src="{image_url}" alt="{topic}"><p>Статья в стиле {style} на тему {topic}...</p>'
    return title, content

def update_existing_post(site_url, username, password, target_url, anchor, topic):
    """
    Fetches the latest posts and attempts to inject a link.
    Safety Valve: Only injects if the post has less than 4 external links.
    """
    auth_string = f"{username}:{password}"
    auth_header = base64.b64encode(auth_string.encode()).decode()
    headers = {'Authorization': f'Basic {auth_header}', 'User-Agent': 'WP-Updater-Bot/1.0'}
    
    endpoint = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts?per_page=5"
    try:
        response = requests.get(endpoint, headers=headers, timeout=15)
        if response.status_code == 200:
            posts = response.json()
            if not posts:
                print(f"   ℹ️  На сайте пока нет старых постов для перелинковки.")
                return False
                
            for post in posts:
                content = post['content']['rendered']
                link_count = content.count("<a ")
                
                if link_count >= 4:
                    continue

                if topic.lower() in content.lower() and target_url not in content:
                    print(f"   🔗 Нашел старый пост для ссылки: {post['link']}")
                    new_content = content.replace(topic, f' <a href="{target_url}">{anchor}</a> ', 1)
                    update_res = requests.post(f"{site_url.rstrip('/')}/wp-json/wp/v2/posts/{post['id']}", 
                                             headers=headers, json={'content': new_content})
                    if update_res.status_code == 200:
                        print("   ✅ Ссылка успешно добавлена в старый пост.")
                        return post['link']
        return False
    except json.JSONDecodeError:
        print("   ⚠️  Сайт ответил не в формате WordPress (возможно, домен припаркован).")
    except Exception:
        # Silently fail for internal linking to not distract from main task
        pass
    return False

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
        target_url = task.get('target_url')
        anchor = task.get('anchor')
        topic = task.get('topic')
        style = task.get('author_style', 'neutral')
        
        if not all([site_url, login, password, target_url, anchor, topic]):
            print(f"Skip task {i+1}: Missing fields.")
            continue
            
        # Feature 3: Try to update existing post first (Internal Linking)
        linked_url = update_existing_post(site_url, login, password, target_url, anchor, topic)
        
        print(f"Generating NEW content (Style: {style}) for topic: {topic}")
        title, content = generate_article(topic, anchor, target_url, style)
        
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
        "site_url": "https://satellite1.com",
        "login": "admin_bot",
        "app_password": "xxxx xxxx xxxx xxxx",
        "target_url": "https://main-project.com/page1",
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
