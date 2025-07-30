import google.generativeai as genai
import openai, os, json, logging

def call_gemini(prompt, key, model="models/gemini-1.5-flash-latest"):
    genai.configure(api_key=key)
    m = genai.GenerativeModel(model)
    resp = m.generate_content({"contents":[{"parts":[{"text": prompt}]}]})
    try:
        return json.loads(resp.text)
    except:
        return {"answer": resp.text}

def call_openai(prompt, key, model="gpt-3.5-turbo"):
    openai.api_key = key
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role":"user","content":prompt}],
        timeout=8
    )
    txt = resp.choices[0].message["content"]
    try:
        return json.loads(txt)
    except:
        return {"answer": txt}
