from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
from datetime import datetime

app = Flask(__name__, static_folder='static') # Garante que a pasta static seja reconhecida
ARQUIVO = "dados.json"

def carregar_dados():
    try:
        with open(ARQUIVO, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] # Retorna lista vazia se o arquivo não existir ou estiver vazio/corrompido

def salvar_dados(dados):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def verificar_vencimentos(dados):
    hoje = datetime.today().date()
    for unidade in dados:
        if unidade.get("locado"):
            fim_str = unidade.get("fim")
            if fim_str: # Verifica se 'fim' existe antes de tentar converter
                fim = datetime.strptime(fim_str, "%Y-%m-%d").date()
                if fim < hoje:
                    # Move a locação para o histórico
                    if "historico_locacoes" not in unidade:
                        unidade["historico_locacoes"] = []
                    
                    # Cria um dicionário para a locação expirada
                    locacao_expirada = {
                        "locatario": unidade.pop("locatario", None),
                        "inicio": unidade.pop("inicio", None),
                        "fim": unidade.pop("fim", None),
                        "data_expiracao": hoje.isoformat() # Adiciona a data em que expirou
                    }
                    unidade["historico_locacoes"].append(locacao_expirada)
                    
                    unidade["locado"] = False
    return dados

# Função auxiliar para formatar datas (já existente, mas importante mencionar)
def formatar_data(data_iso):
    if data_iso:
        try:
            return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            return data_iso # Retorna o original se o formato for inválido
    return ""

# Nova função para coletar todos os itens do histórico de locações
def coletar_historico_completo(dados):
    historico_completo = []
    for unidade in dados:
        if "historico_locacoes" in unidade and unidade["historico_locacoes"]:
            for locacao_historico in unidade["historico_locacoes"]:
                # Adiciona informações da unidade ao item do histórico
                item_historico = {
                    "unidade": unidade.get("unidade"),
                    "apartamento": unidade.get("apartamento"),
                    "proprietario": unidade.get("proprietario"),
                    "locatario": locacao_historico.get("locatario"),
                    "inicio": formatar_data(locacao_historico.get("inicio")),
                    "fim": formatar_data(locacao_historico.get("fim")),
                    "data_evento": formatar_data(locacao_historico.get("data_expiracao") or locacao_historico.get("data_remocao"))
                }
                historico_completo.append(item_historico)
    # Opcional: ordenar o histórico por data
    historico_completo.sort(key=lambda x: datetime.strptime(x["data_evento"], "%d/%m/%Y"), reverse=True)
    return historico_completo


@app.route("/")
def index():
    dados = carregar_dados()
    dados = verificar_vencimentos(dados)
    salvar_dados(dados)
    
    locadas = [u for u in dados if u.get("locado")]
    for u in locadas:
        if u.get("inicio"):
            u["inicio_formatado"] = formatar_data(u["inicio"])
        if u.get("fim"):
            u["fim_formatado"] = formatar_data(u["fim"])
    return render_template("index.html", resultados=locadas)

@app.route("/adicionar-unidade", methods=["GET", "POST"])
def adicionar_unidade():
    if request.method == "POST":
        bloco = request.form["bloco"]
        numero = request.form["numero"]
        proprietario = request.form["proprietario"]

        nova = {
            "unidade": f"{bloco} | {numero}",
            "apartamento": f"Casa {numero}",
            "proprietario": proprietario,
            "locado": False,
            "historico_locacoes": [] # Inicializa o histórico de locações
        }

        dados = carregar_dados()
        dados.append(nova)
        salvar_dados(dados)
        return redirect(url_for("index"))

    return render_template("adicionar_unidade.html")

@app.route("/adicionar-locacao", methods=["GET", "POST"])
def adicionar_locacao():
    dados = carregar_dados()
    unidades_disponiveis = [u for u in dados if not u.get("locado")]

    if request.method == "POST":
        unidade_nome = request.form["unidade"]
        locatario = request.form["locatario"]
        inicio = request.form["inicio"]
        fim = request.form["fim"]

        for u in dados:
            if u["unidade"] == unidade_nome:
                u["locado"] = True
                u["locatario"] = locatario
                u["inicio"] = inicio
                u["fim"] = fim
                break 

        salvar_dados(dados)
        return redirect(url_for("index"))

    return render_template("adicionar_locacao.html", unidades=unidades_disponiveis)

@app.route("/remover-locacao", methods=["GET", "POST"])
def remover_locacao():
    dados = carregar_dados()
    unidades_locadas = [u for u in dados if u.get("locado")]

    if request.method == "POST":
        unidade_nome = request.form["unidade"]

        for u in dados:
            if u["unidade"] == unidade_nome:
                # Move a locação atual para o histórico antes de remover
                if "locatario" in u and "inicio" in u and "fim" in u:
                    if "historico_locacoes" not in u:
                        u["historico_locacoes"] = []
                    locacao_removida = {
                        "locatario": u.pop("locatario"),
                        "inicio": u.pop("inicio"),
                        "fim": u.pop("fim"),
                        "data_remocao": datetime.today().date().isoformat() # Data da remoção manual
                    }
                    u["historico_locacoes"].append(locacao_removida)

                u["locado"] = False
                break 

        salvar_dados(dados)
        return redirect(url_for("index"))

    return render_template("remover_locacao.html", unidades=unidades_locadas)

@app.route("/buscar", methods=["POST"])
def buscar():
    termo = request.json.get("termo", "").lower()
    dados = carregar_dados() 
    
    resultados_filtrados = []
    for u in dados:
        match = False
        if termo in u["unidade"].lower() or \
           termo in u["apartamento"].lower() or \
           termo in u["proprietario"].lower():
            match = True
        
        if u.get("locado") and u.get("locatario") and termo in u["locatario"].lower():
            match = True
        
        if match:
            # Formata as datas para o resultado da busca
            if u.get("inicio"):
                u["inicio_formatado"] = formatar_data(u["inicio"])
            if u.get("fim"):
                u["fim_formatado"] = formatar_data(u["fim"])
            resultados_filtrados.append(u)

    return jsonify(resultados_filtrados)

# Nova rota para o histórico de locações
@app.route("/historico-locacoes")
def historico_locacoes():
    dados = carregar_dados()
    historico = coletar_historico_completo(dados)
    return render_template("historico_locacoes.html", historico=historico)


if __name__ == "__main__":
    app.run(debug=True)