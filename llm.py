"""Модуль анализа фото через нейронку (OpenAI API).

Функции:
  analyze_photos(photo_paths: list[str]) -> dict
    Отправить промпт + фото в нейронку, вернуть распарсенный JSON.
"""

import base64
import json
import os

PROMPT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "prompt_pallet_inspection.txt")
MODEL = "gpt-4o"  # умеет смотреть картинки


def _load_prompt() -> str:
    with open(PROMPT_PATH, encoding="utf-8") as f:
        return f.read()


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_photos(photo_paths: list[str]) -> dict:
    """Отправить фото + промпт в нейронку. Вернёт dict с ответом."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError(
            "openai не установлена. Выполни: pip install openai"
        )

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Не задан OPENAI_API_KEY. "
            "Задай: set OPENAI_API_KEY=sk-..."
        )

    client = OpenAI(api_key=api_key)
    prompt = _load_prompt()

    content = [{"type": "text", "text": prompt}]
    for path in photo_paths:
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{_encode_image(path)}"},
        })

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": content}],
        max_tokens=200,
        temperature=0,
    )

    text = response.choices[0].message.content.strip()
    # Вытаскиваем JSON (вдруг нейронка обернёт в ```json ... ```)
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)