from chatbot_rag.retriever import Retriever
from dotenv import load_dotenv
load_dotenv()    

from chatbot_rag.llm import answer


r = Retriever()
resultados = r.search("Qual o valor dos brigadeiros alcoolicos?")

for c in resultados:
    print(round(c["score"], 3), "| página", c["page"], "|", c["text"][:100])

print(answer("Qual o valor dos brigadeiros alcoolicos?", resultados))

