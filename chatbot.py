import json
import requests
import time
import os
import re

API_KEY = os.getenv("OPENROUTER_API_KEY")  # Lấy từ biến môi trường
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "openai/gpt-3.5-turbo"

# Load knowledge base
with open("knowledge_base.json", "r", encoding="utf-8") as f:
    knowledge_base = json.load(f)

def truncate_answer(text, max_sentences=2):
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) > max_sentences:
        return '. '.join(sentences[:max_sentences]) + '.'
    return text

def retrieve_relevant(user_input, top_k=3):
    user_words = set(user_input.lower().split())
    scored = []
    for item in knowledge_base:
        item_words = set(item['text'].lower().split())
        score = len(user_words & item_words)
        if score > 0:
            scored.append((score, item['text']))
    scored.sort(reverse=True)
    return [text for _, text in scored[:top_k]]

def get_response(user_input, retries=2, max_sentences=2):
    if not user_input.strip() or user_input == "__init__":
        return "Xin chào 👋! Tôi là Galaxy Bot – trợ lý của bạn. Tôi hỗ trợ kiến thức về vũ trụ và thông tin từ trang web này."

    context_texts = retrieve_relevant(user_input)
    context = "\n".join(context_texts)

    prompt = f"Bạn là Galaxy Bot. Dựa trên các thông tin sau từ website:\n{context}\nHãy trả lời ngắn gọn, tối đa 2 câu: {user_input}"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150
    }

    for i in range(retries):
        try:
            response = requests.post(API_URL, json=data, headers=headers, timeout=10)
            resp_json = response.json()
            if "choices" in resp_json:
                text = resp_json["choices"][0]["message"]["content"]
                return truncate_answer(text, max_sentences=max_sentences)
            elif resp_json.get("error", {}).get("code") == 429:
                print(f"Rate limit reached, retrying in 2s... ({i+1}/{retries})")
                time.sleep(2)
            elif "error" in resp_json:
                return f"Lỗi API: {resp_json['error'].get('message', resp_json['error'])}"
        except Exception as e:
            print(f"Exception: {e}")
            time.sleep(2)
    return "API đang quá tải, vui lòng thử lại sau."
