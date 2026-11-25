from anthropic import Anthropic
from chatbot_rag.config import CLAUDE_MODEL

client = Anthropic()

SYSTEM_PROMPT = (
    "Você é um assistente que responde perguntas usando APENAS o contexto fornecido. "
    "Se a resposta não estiver no contexto, diga que não encontrou essa informação no documento. "
    "Cite as fontes no formato [n] correspondente aos trechos usados. Responda em português."
)

def build_context(chunks: list[dict]) -> str:
    parts = []
    for n, c in enumerate(chunks, start=1):
        parts.append(f"[{n}] ({c['source']}, página {c['page']})\n{c['text']}")
    return "\n\n".join(parts)

def answer(question: str, chunks: list[dict]) -> str:
    user_msg = (
        f"<contexto>\n{build_context(chunks)}\n</contexto>\n\n"
        f"Pergunta: {question}"
    )

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,     
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    return response.content[0].text