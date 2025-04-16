from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pymssql
import bcrypt

app = Flask(__name__, static_folder='static')
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
    for numero, participante in resultados:
        numeros.append({"numero": numero, "participante": participante})

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
        return jsonify({"mensagem": "Dados incompletos.", "success": False}), 400

    nome_participante = nome_participante.strip()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT Id FROM Participantes WHERE LOWER(Nome) = LOWER(%s)",
        (nome_participante,)
    )
    row = cursor.fetchone()
    if not row:
        return jsonify({"mensagem": "Participante não encontrado.", "success": False}), 404

    id_participante = row[0]

    cursor.execute(
        "SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante = %s",
        (id_participante,)
    )
    qtd_numeros = cursor.fetchone()[0]
    if qtd_numeros >= 4:
        return jsonify({"mensagem": "Você já comprou 4 números. Limite atingido!", "success": False}), 403

    cursor.execute(
        "SELECT IdParticipante FROM NumerosRifa WHERE Numero = %s",
        (numero,)
    )
    checar = cursor.fetchone()
    if checar and checar[0] is not None:
        return jsonify({"mensagem": f"Número {numero} já foi comprado!", "success": False}), 400

    cursor.execute(
        "UPDATE NumerosRifa SET IdParticipante = %s, DataCompra = GETDATE() WHERE Numero = %s",
        (id_participante, numero)
    )
    conn.commit()
    return jsonify({"mensagem": f"Número {numero} comprado com sucesso por {nome_participante}!", "success": True})

@app.route('/registrar', methods=['POST'])
def registrar():
    try:
        dados = request.get_json()
        nome = dados.get('nome')
        senha = dados.get('senha')

        if not nome or not senha:
            return jsonify({"mensagem": "Preencha nome e senha.", "success": False}), 400

        nome = nome.strip()
        cursor = conn.cursor()

        # Verifica existência
        cursor.execute(
            "SELECT Id FROM Participantes WHERE LOWER(Nome) = LOWER(%s)",
            (nome,)
        )
        if cursor.fetchone():
            return jsonify({"mensagem": "Este nome já está em uso. Escolha outro.", "success": False}), 409

        # Gera próximo Id
        cursor.execute("SELECT ISNULL(MAX(Id), 0) + 1 FROM Participantes")
        next_id = cursor.fetchone()[0]

        # Gera e decodifica o hash
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Insere com Id explícito
        cursor.execute(
            "INSERT INTO Participantes (Id, Nome, SenhaHash) VALUES (%s, %s, %s)",
            (next_id, nome, senha_hash)
        )
        conn.commit()

        return jsonify({"mensagem": f"Cadastro realizado com sucesso para {nome}!", "success": True})

    except Exception as e:
        print("❌ Erro no registrar:", e)
        return jsonify({"mensagem": "Erro interno no servidor.", "success": False}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        dados = request.get_json()
        nome = dados.get('nome')
        senha = dados.get('senha')

        if not nome or not senha:
            return jsonify({"mensagem": "Preencha nome e senha.", "success": False}), 400

        cursor = conn.cursor()
        cursor.execute(
            "SELECT SenhaHash FROM Participantes WHERE Nome = %s",
            (nome,)
        )
        resultado = cursor.fetchone()
        if not resultado:
            return jsonify({"mensagem": "Participante não encontrado.", "success": False}), 404

        senha_hash = resultado[0]
        if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
            return jsonify({"mensagem": "Login realizado com sucesso!", "success": True, "nome": nome})
        else:
            return jsonify({"mensagem": "Senha incorreta.", "success": False}), 401

    except Exception as e:
        print("❌ Erro no login:", e)
        return jsonify({"mensagem": "Erro interno no servidor.", "success": False}), 500

@app.route('/login')
def pagina_login():
    return send_from_directory('static', 'login.html')

@app.route('/register')
def pagina_register():
    return send_from_directory('static', 'register.html')



if __name__ == '__main__':
    app.run(debug=True)


