from fastapi import FastAPI
from openai import OpenAI
import os
import json
import re
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================
load_dotenv()

app = FastAPI()

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

MODEL = os.getenv("MODEL")

# =========================
# CACHE (estoque de perguntas)
# =========================
cache_perguntas = {}

# =========================
# GERAR VÁRIAS PERGUNTAS
# =========================
def gerar_perguntas(materia, quantidade=5):
    prompt = f"""
Gere {quantidade} questões de concurso sobre: {materia}.

Varie entre fácil, médio e difícil.

Responda APENAS em JSON (lista):

[
  {{
    "pergunta": "...",
    "alternativas": ["A","B","C","D"],
    "correta": 0,
    "explicacao": "..."
  }}
]
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.8,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = response.choices[0].message.content
    texto = re.sub(r"```json|```", "", texto).strip()

    try:
        perguntas = json.loads(texto)
        return perguntas
    except:
        raise Exception("Erro ao gerar lista de perguntas")

# =========================
# PEGAR 1 PERGUNTA (com cache)
# =========================
def pegar_pergunta(materia):
    # cria cache se não existir
    if materia not in cache_perguntas:
        cache_perguntas[materia] = []

    # se acabou, gera mais
    if len(cache_perguntas[materia]) == 0:
        novas = gerar_perguntas(materia, 5)
        cache_perguntas[materia].extend(novas)

    # entrega 1 pergunta
    return cache_perguntas[materia].pop(0)

# =========================
# ROTAS
# =========================

@app.get("/")
def home():
    return {"msg": "API rodando 🚀"}

@app.get("/pergunta")
def get_pergunta(materia: str):
    try:
        return pegar_pergunta(materia)
    except Exception as e:
        return {"erro": str(e)}

@app.get("/lote")
def get_lote(materia: str):
    try:
        return gerar_perguntas(materia, 5)
    except Exception as e:
        return {"erro": str(e)}