from base64 import b64decode
from bs4 import BeautifulSoup
import requests
from docx import Document
from googlesearch import search


def save_image(b64_image):
    """Сохранить картинку на диск."""

    with open('generated_files/image.jpg', 'wb') as file:
        file.write(b64decode(b64_image))

def get_url_of_article(query, num_results=1):
    """Найти страницы со статьей по заданному запросу и получить url страницы."""

    search_result = search(query, num_results=num_results)
    url_of_article = next(search_result)
    return url_of_article

def save_short_text(text):
    """Сохранить на диск текст для генерации картинки."""

    with open('generated_files/text_for_image.txt', 'w') as file:
        file.write(text)

def save_text_for_blog(text):
    """Сохранить на диск текст для блога."""

    document = Document()
    document.add_paragraph(text)
    document.save('generated_files/text_for_blog.docx')

def get_html_article_text(url):
    """Получить текст статьи с сайта."""

    result = requests.get(url)
    return result.text

def clean_html_text(text):
    """Очистить переданный html текст от тегов и пробелов."""

    soup = BeautifulSoup(text, features="html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    cleaned_text = soup.get_text()

    lines = (line.strip() for line in cleaned_text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)

    return cleaned_text
