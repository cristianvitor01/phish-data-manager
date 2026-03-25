from flask import Flask, render_template, request, jsonify, Response
from datetime import datetime
import csv
import io
import json

from supabase_client import (
    listar_mensagens,
    criar_mensagem,
    buscar_mensagem,
    atualizar_mensagem,
    deletar_mensagem,
    stats_mensagens,
)

app = Flask(__name__)


CAMPOS_OBRIGATORIOS = {"texto", "classificacao", "tipo_golpe", "fonte", "origem"}
CLASSIFICACOES_VALIDAS = {"fraude", "legitima", "suspeita"}
ORIGENS_VALIDAS = {"simulada", "real", "dataset", "coleta_pessoal"}


def erro_json(mensagem, status=400):
    return jsonify({"erro": mensagem}), status


def normalizar_payload(dados: dict, parcial: bool = False):
    if not isinstance(dados, dict):
        raise ValueError("JSON inválido ou ausente.")

    payload = {}

    campos_permitidos = {
        "texto",
        "classificacao",
        "tipo_golpe",
        "fonte",
        "observacoes",
        "revisada",
        "origem",
    }

    for chave, valor in dados.items():
        if chave in campos_permitidos:
            payload[chave] = valor

    if not parcial:
        faltando = [campo for campo in CAMPOS_OBRIGATORIOS if not payload.get(campo)]
        if faltando:
            raise ValueError(f"Campos obrigatórios ausentes: {', '.join(faltando)}")

    if "classificacao" in payload:
        if payload["classificacao"] not in CLASSIFICACOES_VALIDAS:
            raise ValueError("classificacao deve ser: fraude, legitima ou suspeita.")

    if "origem" in payload:
        if payload["origem"] not in ORIGENS_VALIDAS:
            raise ValueError("origem deve ser: simulada, real, dataset ou coleta_pessoal.")

    if "revisada" in payload:
        payload["revisada"] = bool(payload["revisada"])

    return payload


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "service": "flask-supabase-api"})


@app.route("/api/mensagens", methods=["GET"])
def listar():
    filtros = {}

    classificacao = request.args.get("classificacao")
    tipo_golpe = request.args.get("tipo_golpe")
    fonte = request.args.get("fonte")
    origem = request.args.get("origem")
    busca = request.args.get("busca")
    revisada = request.args.get("revisada")

    if classificacao and classificacao != "todos":
        filtros["classificacao"] = classificacao

    if tipo_golpe and tipo_golpe != "todos":
        filtros["tipo_golpe"] = tipo_golpe

    if fonte and fonte != "todos":
        filtros["fonte"] = fonte

    if origem and origem != "todos":
        filtros["origem"] = origem

    if busca:
        filtros["busca"] = busca

    if revisada is not None and revisada != "":
        if revisada.lower() in {"1", "true", "sim"}:
            filtros["revisada"] = True
        elif revisada.lower() in {"0", "false", "nao", "não"}:
            filtros["revisada"] = False

    try:
        data = listar_mensagens(filtros=filtros)
        return jsonify(data)
    except Exception as e:
        return erro_json(str(e), 500)


@app.route("/api/mensagens", methods=["POST"])
def criar():
    try:
        dados = request.get_json(silent=True) or {}

        dados.pop("id", None)
        dados.pop("data_cadastro", None)

        payload = normalizar_payload(dados, parcial=False)
        payload["data_cadastro"] = datetime.now().strftime("%Y-%m-%d")
        payload.setdefault("revisada", False)

        registros = criar_mensagem(payload)

        if not registros:
            return erro_json("Falha ao criar mensagem.", 500)

        return jsonify(registros[0]), 201
    except ValueError as e:
        return erro_json(str(e), 400)
    except Exception as e:
        return erro_json(str(e), 500)


@app.route("/api/mensagens/<int:mensagem_id>", methods=["GET"])
def detalhe(mensagem_id):
    try:
        registro = buscar_mensagem(mensagem_id)

        if not registro:
            return erro_json("Não encontrado.", 404)

        return jsonify(registro)
    except Exception as e:
        return erro_json(str(e), 500)


@app.route("/api/mensagens/<int:mensagem_id>", methods=["PUT"])
def editar(mensagem_id):
    try:
        dados = request.get_json(silent=True) or {}
        dados.pop("data_cadastro", None)
        dados.pop("id", None)

        payload = normalizar_payload(dados, parcial=True)

        if not payload:
            return erro_json("Nenhum campo válido enviado para atualização.", 400)

        registros = atualizar_mensagem(mensagem_id, payload)

        if not registros:
            return erro_json("Não encontrado.", 404)

        return jsonify(registros[0])
    except ValueError as e:
        return erro_json(str(e), 400)
    except Exception as e:
        return erro_json(str(e), 500)


@app.route("/api/mensagens/<int:mensagem_id>", methods=["DELETE"])
def excluir(mensagem_id):
    try:
        registros = deletar_mensagem(mensagem_id)

        if not registros:
            return erro_json("Não encontrado.", 404)

        return jsonify({"ok": True})
    except Exception as e:
        return erro_json(str(e), 500)


@app.route("/api/stats", methods=["GET"])
def stats():
    try:
        resultado = stats_mensagens()
        return jsonify(resultado)
    except Exception as e:
        return erro_json(str(e), 500)


@app.route("/api/export/csv", methods=["GET"])
def export_csv():
    try:
        rows = listar_mensagens()

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            "id",
            "texto",
            "classificacao",
            "tipo_golpe",
            "fonte",
            "origem",
            "data_cadastro",
            "observacoes",
            "revisada",
        ])

        for r in rows:
            writer.writerow([
                r.get("id"),
                r.get("texto"),
                r.get("classificacao"),
                r.get("tipo_golpe"),
                r.get("fonte"),
                r.get("origem"),
                r.get("data_cadastro"),
                r.get("observacoes"),
                r.get("revisada"),
            ])

        csv_content = output.getvalue()
        output.close()

        return Response(
            csv_content,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=dataset.csv"},
        )
    except Exception as e:
        return erro_json(str(e), 500)


@app.route("/api/export/json", methods=["GET"])
def export_json():
    try:
        data = listar_mensagens()

        return Response(
            json.dumps(data, ensure_ascii=False, indent=2),
            mimetype="application/json; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=dataset.json"},
        )
    except Exception as e:
        return erro_json(str(e), 500)


if __name__ == "__main__":
    app.run(debug=True, port=5000)