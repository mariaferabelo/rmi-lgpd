import json
import pandas as pd

# --- 1. Total de ocorrências por termo (global) ---
with open("indice.json", "r", encoding="utf-8") as f:
    indice_invertido = json.load(f)

total_ocorrencias = {}
for termo, docs in indice_invertido.items():
    total_ocorrencias[termo] = sum(docs.values())

with open("total_ocorrencias.json", "w", encoding="utf-8") as f:
    json.dump(total_ocorrencias, f, ensure_ascii=False, indent=2)

# --- 2. Carregar TF.xlsx (colunas: Artigo 01, Artigo 02, ...) ---
tf_df = pd.read_excel("TF.xlsx")
tf_df = tf_df.set_index("Termo")  # Nome exato da primeira coluna

# --- 3. Carregar metadados (DocId com espaço!) ---
with open("metadados.json", "r", encoding="utf-8") as f:
    metadados = json.load(f)

tabela_documentos = []
for doc in metadados:
    doc_id = doc["DocId"]  # Ex: "Artigo 01"
    if doc_id in tf_df.columns:
        total_termos = int(tf_df[doc_id].sum())
    else:
        total_termos = 0
        print(f"AVISO: {doc_id} não encontrado no TF.xlsx")
    
    tabela_documentos.append({
        "DocId": doc_id,
        "Titulo": doc["Titulo"],
        "Autores": doc["Autores"],
        "TotalTermosSignificativos": total_termos
    })

with open("tabela_documentos.json", "w", encoding="utf-8") as f:
    json.dump(tabela_documentos, f, ensure_ascii=False, indent=2)

# --- 4. Registro final ---
ultimo_doc = tabela_documentos[-1]["DocId"]
total_palavras = sum(doc["TotalTermosSignificativos"] for doc in tabela_documentos)

registro_final = {
    "UltimoDocId": ultimo_doc,
    "TotPal": total_palavras
}

with open("registro_final.json", "w", encoding="utf-8") as f:
    json.dump(registro_final, f, ensure_ascii=False, indent=2)

print("MÓDULO 2 CONCLUÍDO!")
print(f"Documentos: {len(tabela_documentos)}")
print(f"Total de palavras significativas: {total_palavras}")
print(f"Último DocId: {ultimo_doc}")