from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
import csv
import os
from datetime import datetime
from supabase_client import listar_mensagens, criar_mensagem, buscar_mensagem, atualizar_mensagem, deletar_mensagem, stats_mensagens

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
EXPORT_DIR = os.path.join(os.path.dirname(__file__), 'export')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS mensagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT NOT NULL,
            classificacao TEXT NOT NULL,
            tipo_golpe TEXT NOT NULL,
            fonte TEXT NOT NULL,
            data_cadastro TEXT NOT NULL,
            observacoes TEXT,
            revisada INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    # Seed sample data if empty
    count = conn.execute('SELECT COUNT(*) FROM mensagens').fetchone()[0]
    if count == 0:
        samples = [
            ("Parabéns! Você foi selecionado para receber R$500 de crédito. Clique aqui: bit.ly/premio123", "fraude", "smishing", "SMS", "2024-01-10", "Mensagem típica de smishing com link encurtado", 1),
            ("Seu banco detectou atividade suspeita. Confirme seus dados agora: www.banco-fake.com", "fraude", "phishing", "Email", "2024-01-12", "Phishing bancário clássico", 1),
            ("Olá! Sua consulta de amanhã às 14h está confirmada. Dúvidas: (85) 3333-4444", "legitima", "outro", "SMS", "2024-01-13", "SMS legítimo de consultório médico", 1),
            ("URGENTE: Sua conta será bloqueada em 24h. Acesse: www.itau-seguro.net para regularizar", "fraude", "phishing", "Email", "2024-01-15", "Phishing se passando por banco Itaú", 0),
            ("Oi! Temos uma oferta especial pra você, 50% off em todos os produtos. Válido hoje!", "suspeita", "scam", "WhatsApp", "2024-01-16", "Possível scam de loja desconhecida", 0),
            ("Lembrete: sua fatura vence amanhã. Valor: R$320,00. Acesse o app para pagar.", "legitima", "outro", "SMS", "2024-01-18", "SMS legítimo de operadora de cartão", 1),
        ]
        conn.executemany(
            'INSERT INTO mensagens (texto, classificacao, tipo_golpe, fonte, data_cadastro, observacoes, revisada) VALUES (?,?,?,?,?,?,?)',
            samples
        )
        conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mensagens', methods=['GET'])
def listar():
    # Suporta os mesmos filtros previstos no SQLite, mas usando Supabase.
    params = {}
    if request.args.get('classificacao') and request.args.get('classificacao') != 'todos':
        params['classificacao'] = request.args.get('classificacao')
    if request.args.get('tipo_golpe') and request.args.get('tipo_golpe') != 'todos':
        params['tipo_golpe'] = request.args.get('tipo_golpe')
    if request.args.get('fonte') and request.args.get('fonte') != 'todos':
        params['fonte'] = request.args.get('fonte')

    if request.args.get('busca'):
        busca = request.args.get('busca')
        data = listar_mensagens()  # Busca completa do Supabase
        data = [m for m in data if busca.lower() in m.get('texto', '').lower()]
    else:
        data = listar_mensagens()

    # Aplicar filtros adicionais em memória (só quando Supabase não fizer todos os filtros).
    for chave, valor in params.items():
        data = [m for m in data if m.get(chave) == valor]

    return jsonify(data)

@app.route('/api/mensagens', methods=['POST'])
def criar():
    d = request.json
    d['data_cadastro'] = datetime.now().strftime('%Y-%m-%d')
    if 'revisada' not in d:
        d['revisada'] = 0

    registros = criar_mensagem(d)
    if not registros:
        return jsonify({'erro': 'Falha ao criar mensagem via Supabase'}), 500

    return jsonify(registros[0]), 201

@app.route('/api/mensagens/<int:id>', methods=['GET'])
def detalhe(id):
    try:
        registro = buscar_mensagem(id)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

    if not registro:
        return jsonify({'erro': 'Não encontrado'}), 404

    return jsonify(registro)

@app.route('/api/mensagens/<int:id>', methods=['PUT'])
def editar(id):
    d = request.json
    if 'data_cadastro' in d:
        d.pop('data_cadastro')

    try:
        registros = atualizar_mensagem(id, d)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

    if not registros:
        return jsonify({'erro': 'Não encontrado'}), 404

    return jsonify(registros[0])

@app.route('/api/mensagens/<int:id>', methods=['DELETE'])
def excluir(id):
    try:
        registros = deletar_mensagem(id)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

    if not registros:
        return jsonify({'erro': 'Não encontrado'}), 404

    return jsonify({'ok': True})

@app.route('/api/stats')
def stats():
    try:
        resultado = stats_mensagens()
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    return jsonify(resultado)

@app.route('/api/export/csv')
def export_csv():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, 'dataset.csv')
    try:
        rows = listar_mensagens()
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['id', 'texto', 'label', 'tipo_golpe', 'fonte', 'data_cadastro', 'revisada'])
        for r in rows:
            w.writerow([
                r.get('id'),
                r.get('texto'),
                r.get('classificacao'),
                r.get('tipo_golpe'),
                r.get('fonte'),
                r.get('data_cadastro'),
                r.get('revisada'),
            ])
    return send_file(path, as_attachment=True, download_name='dataset.csv')


@app.route('/api/export/json')
def export_json():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, 'dataset.json')
    try:
        data = listar_mensagens()
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return send_file(path, as_attachment=True, download_name='dataset.json')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
