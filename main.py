from fastapi import FastAPI
from openai import OpenAI
from supabase import create_client
import os
import json
import re
from dotenv import load_dotenv

# =========================
# CONFIG
# =========================
load_dotenv()

app = FastAPI()

# 🔑 OpenAI / Groq
client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)

MODEL = os.getenv("MODEL")

# 🔑 Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# =========================
# BUSCAR NO BANCO
# =========================
def buscar_questao(disciplina):
    try:
        response = (
            supabase
            .table("questoes")
            .select("*")
            .eq("disciplina", disciplina.lower())
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]

        return None

    except Exception as e:
        print("Erro ao buscar:", e)
        return None


# =========================
# SALVAR NO BANCO
# =========================
def salvar_questao(q, disciplina):
    try:
        supabase.table("questoes").insert({
            "disciplina": disciplina.lower(),
            "banca": q.get("banca"),
            "nivel": q.get("nivel"),
            "pergunta": q["pergunta"],
            "alternativas": q["alternativas"],
            "resposta_correta": q["correta"],
            "explicacao": q["explicacao"]
        }).execute()

    except Exception as e:
        print("Erro ao salvar:", e)


# =========================
# GERAR COM IA
# =========================
def gerar_pergunta(disciplina):

    prompt = f"""
Gere 1 questão de concurso sobre {disciplina}.

Retorne APENAS JSON:

{{
  "pergunta": "...",
  "alternativas": ["A","B","C","D"],
  "correta": 0,
  "explicacao": "...",
  "banca": "FGV",
  "nivel": "medio"
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = response.choices[0].message.content
    texto = re.sub(r"```json|```", "", texto).strip()

    return json.loads(texto)


# =========================
# ENDPOINT PRINCIPAL
# =========================
@app.get("/pergunta")
def get_pergunta(disciplina: str):

    # 1️⃣ tenta banco
    questao = buscar_questao(disciplina)

    if questao:
        return questao

    # 2️⃣ se não tiver → IA
    nova = gerar_pergunta(disciplina)

    # 3️⃣ salva no banco
    salvar_questao(nova, disciplina)

    return nova
