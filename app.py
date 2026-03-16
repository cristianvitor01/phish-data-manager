from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
import csv
import os
from datetime import datetime

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
    conn = get_db()
    q = 'SELECT * FROM mensagens WHERE 1=1'
    params = []
    for campo, col in [('classificacao','classificacao'),('tipo_golpe','tipo_golpe'),('fonte','fonte')]:
        val = request.args.get(campo)
        if val and val != 'todos':
            q += f' AND {col} = ?'
            params.append(val)
    busca = request.args.get('busca')
    if busca:
        q += ' AND texto LIKE ?'
        params.append(f'%{busca}%')
    q += ' ORDER BY id DESC'
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/mensagens', methods=['POST'])
def criar():
    d = request.json
    conn = get_db()
    cur = conn.execute(
        'INSERT INTO mensagens (texto, classificacao, tipo_golpe, fonte, data_cadastro, observacoes, revisada) VALUES (?,?,?,?,?,?,?)',
        (d['texto'], d['classificacao'], d['tipo_golpe'], d['fonte'],
         datetime.now().strftime('%Y-%m-%d'), d.get('observacoes',''), d.get('revisada',0))
    )
    conn.commit()
    row = conn.execute('SELECT * FROM mensagens WHERE id=?', (cur.lastrowid,)).fetchone()
    conn.close()
    return jsonify(dict(row)), 201

@app.route('/api/mensagens/<int:id>', methods=['GET'])
def detalhe(id):
    conn = get_db()
    row = conn.execute('SELECT * FROM mensagens WHERE id=?', (id,)).fetchone()
    conn.close()
    if not row: return jsonify({'erro':'Não encontrado'}), 404
    return jsonify(dict(row))

@app.route('/api/mensagens/<int:id>', methods=['PUT'])
def editar(id):
    d = request.json
    conn = get_db()
    conn.execute(
        'UPDATE mensagens SET texto=?, classificacao=?, tipo_golpe=?, fonte=?, observacoes=?, revisada=? WHERE id=?',
        (d['texto'], d['classificacao'], d['tipo_golpe'], d['fonte'], d.get('observacoes',''), d.get('revisada',0), id)
    )
    conn.commit()
    row = conn.execute('SELECT * FROM mensagens WHERE id=?', (id,)).fetchone()
    conn.close()
    return jsonify(dict(row))

@app.route('/api/mensagens/<int:id>', methods=['DELETE'])
def excluir(id):
    conn = get_db()
    conn.execute('DELETE FROM mensagens WHERE id=?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/stats')
def stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM mensagens').fetchone()[0]
    fraudes = conn.execute("SELECT COUNT(*) FROM mensagens WHERE classificacao='fraude'").fetchone()[0]
    legitimas = conn.execute("SELECT COUNT(*) FROM mensagens WHERE classificacao='legitima'").fetchone()[0]
    suspeitas = conn.execute("SELECT COUNT(*) FROM mensagens WHERE classificacao='suspeita'").fetchone()[0]
    revisadas = conn.execute("SELECT COUNT(*) FROM mensagens WHERE revisada=1").fetchone()[0]
    por_tipo = {}
    for row in conn.execute("SELECT tipo_golpe, COUNT(*) as c FROM mensagens GROUP BY tipo_golpe"):
        por_tipo[row['tipo_golpe']] = row['c']
    por_fonte = {}
    for row in conn.execute("SELECT fonte, COUNT(*) as c FROM mensagens GROUP BY fonte"):
        por_fonte[row['fonte']] = row['c']
    conn.close()
    return jsonify({'total':total,'fraudes':fraudes,'legitimas':legitimas,'suspeitas':suspeitas,'revisadas':revisadas,'por_tipo':por_tipo,'por_fonte':por_fonte})

@app.route('/api/export/csv')
def export_csv():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, 'dataset.csv')
    conn = get_db()
    rows = conn.execute('SELECT id, texto, classificacao AS label, tipo_golpe, fonte, data_cadastro, revisada FROM mensagens ORDER BY id').fetchall()
    conn.close()
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['id','texto','label','tipo_golpe','fonte','data_cadastro','revisada'])
        for r in rows:
            w.writerow(list(r))
    return send_file(path, as_attachment=True, download_name='dataset.csv')

@app.route('/api/export/json')
def export_json():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    path = os.path.join(EXPORT_DIR, 'dataset.json')
    conn = get_db()
    rows = conn.execute('SELECT id, texto, classificacao AS label, tipo_golpe, fonte, data_cadastro, revisada FROM mensagens ORDER BY id').fetchall()
    conn.close()
    data = [dict(r) for r in rows]
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return send_file(path, as_attachment=True, download_name='dataset.json')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
