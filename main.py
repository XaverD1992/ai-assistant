import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

from prompts import get_prompt_for_generating_text_for_blog, get_prompt_for_generating_short_phrase_for_image, \
    get_prompt_for_generating_image
from helper_functions import save_text_for_blog, get_html_article_text, clean_html_text, save_short_text, save_image, \
    get_url_of_article
from constants import query

load_dotenv()

api_key = os.getenv('API_KEY')

openai_client = OpenAI(api_key=api_key)

def generate_image(prompt):
    """Сгенерировать картинку от gpt модели на основании переданного промпта."""

    response = openai_client.images.generate(
        n=1,
        size="512x512",
        response_format="b64_json",
        prompt=prompt
    )
    return response.data[0].b64_json


available_functions = {
    "generate_image": generate_image
}


assistant = openai_client.beta.assistants.create(
    name="Генератор текстов и изображений.",
    instructions="Ты должен генерировать тексты для блога на основании статей, выделять и генерировать "
                 "основную мысль из текста, а также генерировать изображение на основании переданного текста. "
                 "Используй переданную функцию для генерации изображения при соответствующем запросе.",
    model="gpt-4o-mini",
    tools=[
    {
      "type": "function",
      "function": {
        "name": "generate_image",
        "description": "Generate image from text",
        "parameters": {
          "type": "object",
          "properties": {
            "prompt": {
              "type": "string",
              "description": "Prompt text for generating image"
            },
          },
          "required": ["prompt"]
        }
      }
    }
    ]
)

def submit_message(assistant_id, thread, user_message):
    """Создать message и запустить run."""
    openai_client.beta.threads.messages.create(
        thread_id=thread.id, role="user", content=user_message
    )
    return openai_client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id,
    )

def create_thread():
    """Создать thread."""
    thread = openai_client.beta.threads.create()
    return thread

def run_thread(user_input, thread):
    """Запустить thread."""
    run = submit_message(assistant.id, thread, user_input)
    return run

def wait_on_run(run, thread):
    """Ожидать завершения выполнения задачи."""
    while run.status == "queued" or run.status == "in_progress":
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)

    if run.status == "requires_action":
        tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        function = available_functions[function_name]
        output = function(**arguments)
        return run, output
    return run


if __name__ == '__main__':

    # получить url изображения
    url = get_url_of_article(query)

    # получить текст по url в html формате
    html_text = get_html_article_text(url)

    # очистить html текст от тегов
    cleaned_text = clean_html_text(html_text)

    # создать thread
    thread = create_thread()

    # задача генерации текста для блога
    run1 = run_thread(get_prompt_for_generating_text_for_blog(cleaned_text), thread)
    run1 = wait_on_run(run1, thread)
    text_for_blog = openai_client.beta.threads.messages.list(thread_id=thread.id, order="asc").data[1].content[0].text.value
    save_text_for_blog(text_for_blog)

    # задача генерации короткого текста для последующей генерации изображения по ней
    run2 = run_thread(get_prompt_for_generating_short_phrase_for_image(text_for_blog), thread)
    run2 = wait_on_run(run2, thread)
    text_for_image = openai_client.beta.threads.messages.list(thread_id=thread.id, order="asc").data[3].content[0].text.value
    save_short_text(text_for_image)

    # задача генерации изображения
    run3 = run_thread(get_prompt_for_generating_image(text_for_image), thread)
    run3, output = wait_on_run(run3, thread)
    save_image(output)
