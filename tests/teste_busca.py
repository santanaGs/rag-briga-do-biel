from chatbot_rag.retriever import Retriever

r = Retriever()
resultados = r.search("Qual o valor dos brigadeiros alcoolicos?")

for c in resultados:
    print(round(c["score"], 3), "| página", c["page"], "|", c["text"][:100])
