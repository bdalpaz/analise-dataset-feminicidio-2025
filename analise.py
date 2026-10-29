import pandas as pd
import matplotlib.pyplot as plt

ARQ1 = "dados/violencia_2024.csv"
ARQ2 = "dados/violencia_2025.csv"
ANO1, ANO2 = "2024", "2025"
FONTE = "Fonte: Ministério da Saúde/SVSA – Sinan Net (DATASUS/TabNet)"

# 1. Leitura: lê cada arquivo do TabNet e junta pelo nome da UF
def ler_tabnet(arquivo, ano):
    d = pd.read_csv(arquivo, sep=";", encoding="latin-1", skiprows=4,
                    engine="python", on_bad_lines="skip")
    d = d.rename(columns={d.columns[0]: "UF"})
    d["UF"] = d["UF"].astype(str)
    fim = d.index[d["UF"].str.strip() == "Total"][0]   # remove o rodapé
    return d.loc[:fim, ["UF", ano]]

df = ler_tabnet(ARQ1, ANO1).merge(ler_tabnet(ARQ2, ANO2), on="UF", how="outer")
linhas_antes = len(df)

# 2. Limpeza
print("Valores ausentes:\n", df.isna().sum())
print("Linhas duplicadas:", df.duplicated().sum())

# Mantém só os estados (linhas que começam com "..") -> remove regiões e Total
df = df[df["UF"].str.startswith("..")].copy()
df["UF"] = df["UF"].str.lstrip(". ").str.strip()

# No TabNet, "-" significa zero; converte para número
for c in [ANO1, ANO2]:
    df[c] = pd.to_numeric(df[c].replace("-", 0), errors="coerce")

df = df.drop_duplicates().dropna(subset=[ANO1, ANO2])
df = df[["UF", ANO1, ANO2]]
df["Variação (%)"] = ((df[ANO2] - df[ANO1]) / df[ANO1] * 100).round(1)
linhas_depois = len(df)
print(f"Linhas antes: {linhas_antes} | depois: {linhas_depois}")

# 3. Estatística descritiva
desc = df[[ANO1, ANO2]].agg(["mean", "median", "std", "min", "max"]).T
desc.columns = ["Média", "Mediana", "Desvio padrão", "Mínimo", "Máximo"]
desc = desc.round(2)
print(desc)

# 4. Planilha
with pd.ExcelWriter("medidas_descritivas.xlsx") as w:
    desc.to_excel(w, sheet_name="Descritivas")
    pd.DataFrame({"Etapa": ["Antes da limpeza", "Depois da limpeza"],
                  "Linhas": [linhas_antes, linhas_depois]}
                 ).to_excel(w, sheet_name="Limpeza", index=False)
    df.to_excel(w, sheet_name="Dados limpos", index=False)

# 5. Gráficos
def finalizar(fig, nome):
    fig.text(0.01, 0.01, FONTE, fontsize=8)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(nome, dpi=150)
    plt.show()

# Gráfico 1: notificações por UF nos dois anos
d = df.sort_values(ANO2)
fig, ax = plt.subplots(figsize=(8, 7.5))
y = range(len(d))
ax.barh([i - 0.2 for i in y], d[ANO1], height=0.4, label=ANO1)
ax.barh([i + 0.2 for i in y], d[ANO2], height=0.4, label=ANO2)
ax.set_yticks(list(y)); ax.set_yticklabels(d["UF"])
ax.set(title="Notificações de violência contra mulheres por UF",
       xlabel="Número de notificações", ylabel="Unidade da Federação")
ax.legend(loc="lower right")
finalizar(fig, "grafico1_barras_uf.png")

# Gráfico 2: variação percentual por UF
d = df.sort_values("Variação (%)")
fig, ax = plt.subplots(figsize=(8, 7.5))
cores = ["tab:red" if v > 0 else "tab:green" for v in d["Variação (%)"]]
ax.barh(d["UF"], d["Variação (%)"], color=cores)
ax.axvline(0, color="black", linewidth=0.8)
ax.set(title=f"Variação das notificações entre {ANO1} e {ANO2}",
       xlabel="Variação (%)", ylabel="Unidade da Federação")
finalizar(fig, "grafico2_variacao.png")

# Gráfico 3: dispersão ANO1 x ANO2 com linha de referência (y = x)
fig, ax = plt.subplots()
ax.scatter(df[ANO1], df[ANO2])
lim = max(df[ANO1].max(), df[ANO2].max()) * 1.05
ax.plot([0, lim], [0, lim], "--", color="gray", label="Sem variação (y = x)")
ax.set(title=f"Notificações por UF: {ANO1} x {ANO2}",
       xlabel=f"Notificações em {ANO1}", ylabel=f"Notificações em {ANO2}")
ax.legend()
finalizar(fig, "grafico3_dispersao.png")

print("Total Brasil:", df[ANO1].sum(), "->", df[ANO2].sum())
print("UFs com aumento:", (df["Variação (%)"] > 0).sum(), "de", len(df))