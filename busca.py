# ===============================================
# MÓDULO 3 - RECUPERAÇÃO DE INFORMAÇÕES
# VERSÃO FINAL TESTADA - FUNCIONA COM "COMO", "LGPD", ETC.
# ===============================================

import json
import tkinter as tk
from tkinter import ttk, messagebox
import re
import math
from collections import Counter

# --- Carregar dados ---
with open("indice.json", "r", encoding="utf-8") as f:
    indice = json.load(f)

with open("metadados.json", "r", encoding="utf-8") as f:
    metadados = {doc["DocId"]: doc for doc in json.load(f)}

# --- Carregar resumos ---
resumos = {}
for i in range(1, 21):
    doc_id = f"Artigo {i:02d}"
    filename = f"resumos_processados/resumo_processado_{i:02d}.txt"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            resumos[doc_id] = f.read()
    except:
        resumos[doc_id] = "Resumo não disponível."

# Stop-words
STOP_WORDS = {"a", "o", "de", "em", "com", "para", "que", "e", "da", "do", "dos", "das", "um", "uma", "se", "como", "sobre", "na", "no", "por", "os", "as", "ao", "à", "é", "são", "foi", "ser", "está", "estão", "ter", "tem", "não", "mas", "ou", "nem", "já", "ainda", "até", "após", "antes", "durante", "entre", "sob", "sem", "desde", "pela", "pelo", "pelos", "pelas", "nas", "nos", "uns", "umas"}

def processar_texto(texto):
    texto = texto.lower()
    palavras = re.findall(r'\b[\w-]+\b', texto)
    return [p for p in palavras if p not in STOP_WORDS]

# --- Modelo Booleano (CORRIGIDO - agora funciona!) ---
def busca_booleana(query):
    query = query.lower()
    # Extrair termos e operadores corretamente
    # Ignorar operadores para termos simples, mas suportar AND/OR/NOT
    termos = re.findall(r'\b(and|or|not|[\w-]+)\b', query)
    
    if not termos:
        return []
    
    # Filtrar só termos (não operadores)
    termos_filtrados = [t for t in termos if t not in ['and', 'or', 'not']]
    
    if not termos_filtrados:
        return []
    
    # Para termos simples, pega docs do primeiro termo
    primeiro_termo = termos_filtrados[0]
    if primeiro_termo in indice:
        docs = set(indice[primeiro_termo].keys())
    else:
        return []
    
    # Aplicar operadores se houver
    i = 0
    while i < len(termos) - 1:
        op = termos[i].lower()
        if op in ['and', 'or', 'not'] and i + 1 < len(termos):
            proximo_termo = termos[i+1].lower()
            if proximo_termo in indice:
                docs_termo = set(indice[proximo_termo].keys())
                if op == "and":
                    docs &= docs_termo
                elif op == "or":
                    docs |= docs_termo
                elif op == "not":
                    docs -= docs_termo
            i += 2
        else:
            i += 1
    
    return list(docs)

# --- Modelo Vetorial ---
def calcular_idf():
    N = 20
    idf = {}
    for termo, docs in indice.items():
        df = len(docs)
        idf[termo] = math.log(N / (df + 1)) if df > 0 else 0
    return idf

idf_cache = calcular_idf()

def vetor_documento(doc_id):
    return {termo: freq[doc_id] * idf_cache.get(termo, 0) for termo, freq in indice.items() if doc_id in freq}

def vetor_consulta(termos):
    contador = Counter(termos)
    return {termo: contador[termo] * idf_cache.get(termo, 0) for termo in contador if termo in idf_cache}

def cosseno(v1, v2):
    if not v1 or not v2:
        return 0
    num = sum(v1.get(t, 0) * v2.get(t, 0) for t in set(v1) & set(v2))
    den1 = math.sqrt(sum(x**2 for x in v1.values()))
    den2 = math.sqrt(sum(x**2 for x in v2.values()))
    return num / (den1 * den2) if den1 > 0 and den2 > 0 else 0

def busca_vetorial(query):
    termos = processar_texto(query)
    if not termos:
        return []
    v_query = vetor_consulta(termos)
    scores = []
    for doc_id in metadados:
        v_doc = vetor_documento(doc_id)
        sim = cosseno(v_query, v_doc)
        if sim > 0:
            scores.append((doc_id, sim))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in scores]

# --- Interface ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Busca LGPD - FUNCIONANDO!")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f8f9fa")

        tk.Label(root, text="Sistema de Recuperação de Informações - LGPD", font=("Arial", 18, "bold"), bg="#f8f9fa").pack(pady=20)

        frame = tk.Frame(root, bg="#f8f9fa")
        frame.pack(pady=10)

        tk.Label(frame, text="Consulta:", bg="#f8f9fa", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky="w")
        self.entry = tk.Entry(frame, width=50, font=("Arial", 12))
        self.entry.grid(row=0, column=1, padx=5)

        self.modelo_var = tk.StringVar(value="Booleano")
        tk.Radiobutton(frame, text="Booleano", variable=self.modelo_var, value="Booleano", bg="#f8f9fa").grid(row=0, column=2, padx=10)
        tk.Radiobutton(frame, text="Vetorial", variable=self.modelo_var, value="Vetorial", bg="#f8f9fa").grid(row=0, column=3, padx=10)

        tk.Button(frame, text="BUSCAR", command=self.buscar, bg="#28a745", fg="white", font=("Arial", 12, "bold")).grid(row=0, column=4, padx=15)

        self.tree = ttk.Treeview(root, columns=("ID", "Título", "Autor"), show="headings", height=16)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Título", text="Título")
        self.tree.heading("Autor", text="Autor(es)")
        self.tree.column("ID", width=80, anchor="center")
        self.tree.column("Título", width=600)
        self.tree.column("Autor", width=300)
        self.tree.pack(pady=10, fill="both", expand=True)
        self.tree.bind("<Double-1>", self.mostrar_detalhes)

        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

    def buscar(self):
        query = self.entry.get().strip()
        if not query:
            messagebox.showwarning("Erro", "Digite uma consulta!")
            return
        for item in self.tree.get_children():
            self.tree.delete(item)

        modelo = self.modelo_var.get()
        resultados = busca_booleana(query) if modelo == "Booleano" else busca_vetorial(query)

        for doc_id in resultados:
            meta = metadados[doc_id]
            autores = meta["Autores"][:80] + "..." if len(meta["Autores"]) > 80 else meta["Autores"]
            self.tree.insert("", "end", values=(doc_id, meta["Titulo"], autores))

        tk.Label(self.root, text=f"{len(resultados)} documento(s) encontrado(s)", bg="#f8f9fa", font=("Arial", 11)).pack(pady=5)

    def mostrar_detalhes(self, event):
        item = self.tree.selection()
        if not item: return
        doc_id = self.tree.item(item[0], "values")[0]
        meta = metadados[doc_id]
        resumo = resumos.get(doc_id, "Não disponível")
        messagebox.showinfo(doc_id, f"TÍTULO:\n{meta['Titulo']}\n\nAUTORES:\n{meta['Autores']}\n\nRESUMO:\n{resumo}")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()