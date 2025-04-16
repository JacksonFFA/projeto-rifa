from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pymssql
import bcrypt

app = Flask(__name__)
CORS(app)

# Conexão com SQL Server - Azure
conn = pymssql.connect(
    server='servidor-rifa.database.windows.net',
    user='adminrifa',
    password='Jk@FFA22',
    database='rifa-db'
)

@app.route('/')
def home():
    return jsonify({"mensagem": "API da Rifa está rodando com sucesso!"})

@app.route('/numeros')
def listar_numeros():
    cursor = conn.cursor()
    query = """
        SELECT
            Numero,
            ISNULL(P.Nome, '') AS NomeParticipante
        FROM NumerosRifa NR
        LEFT JOIN Participantes P ON NR.IdParticipante = P.Id
        ORDER BY Numero
    """
    cursor.execute(query)
    resultados = cursor.fetchall()

    numeros = []
    for row in resultados:
        numeros.append({
            "numero": row.Numero,
            "participante": row.NomeParticipante
        })

    return jsonify(numeros)

@app.route('/front')
def front():
    return send_from_directory('static', 'index.html')

@app.route('/comprar', methods=['POST'])
def comprar_numero():
    dados = request.get_json()
    numero = dados.get('numero')
    nome_participante = dados.get('participante')

    if not numero or not nome_participante:
        return jsonify({"mensagem": "Dados incompletos."}), 400

    nome_participante = nome_participante.strip()
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Participantes WHERE LOWER(Nome) = LOWER(?)", nome_participante)
    resultado = cursor.fetchone()

    if not resultado:
        return jsonify({"mensagem": "Participante não encontrado."}), 404

    id_participante = resultado.Id

    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante = ?", id_participante)
    qtd_numeros = cursor.fetchone()[0]

    if qtd_numeros >= 4:
        return jsonify({"mensagem": "Você já comprou 4 números. Limite atingido!"}), 403

    cursor.execute("SELECT IdParticipante FROM NumerosRifa WHERE Numero = ?", numero)
    checar = cursor.fetchone()
    if checar and checar.IdParticipante is not None:
        return jsonify({"mensagem": f"Número {numero} já foi comprado!"}), 400

    cursor.execute(
        "UPDATE NumerosRifa SET IdParticipante = ?, DataCompra = GETDATE() WHERE Numero = ?",
        id_participante, numero
    )
    conn.commit()

    return jsonify({"mensagem": f"Número {numero} comprado com sucesso por {nome_participante}!"})

@app.route('/registrar', methods=['POST'])
def registrar():
    dados = request.get_json()
    nome = dados.get('nome')
    senha = dados.get('senha')

    if not nome or not senha:
        return jsonify({"mensagem": "Preencha nome e senha."}), 400

    nome = nome.strip()
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Participantes WHERE LOWER(Nome) = LOWER(?)", nome)
    resultado = cursor.fetchone()

    if resultado:
        return jsonify({"mensagem": "Este nome já está em uso. Escolha outro."}), 409

    senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())

    cursor.execute(
        "INSERT INTO Participantes (Nome, SenhaHash) VALUES (?, ?)",
        nome, senha_hash
    )
    conn.commit()

    return jsonify({"mensagem": f"Cadastro realizado com sucesso para {nome}!"})

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    nome = dados.get('nome')
    senha = dados.get('senha')

    if not nome or not senha:
        return jsonify({"mensagem": "Preencha nome e senha.", "success": False}), 400

    cursor = conn.cursor()
    cursor.execute("SELECT SenhaHash FROM Participantes WHERE Nome = ?", nome)
    resultado = cursor.fetchone()

    if not resultado:
        return jsonify({"mensagem": "Participante não encontrado.", "success": False}), 404

    senha_hash = resultado[0]

    if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
        return jsonify({"mensagem": "Login realizado com sucesso!", "success": True, "nome": nome})
    else:
        return jsonify({"mensagem": "Senha incorreta.", "success": False}), 401

@app.route('/login')
def pagina_login():
    return send_from_directory('static', 'login.html')

@app.route('/register')
def pagina_register():
    return send_from_directory('static', 'register.html')


# 👇 Isso deve ficar no final
if __name__ == '__main__':
    app.run(debug=True)



