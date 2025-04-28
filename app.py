from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pyodbc
import bcrypt
import os
import time
from dotenv import load_dotenv
from routes.dashboard import dashboard_bp

# Carrega variáveis do .env local, se existir
if os.path.exists('.env'):
    load_dotenv()

# Inicializa app Flask
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Registra blueprint do dashboard
dashboard_bp.template_folder = 'templates'
app.register_blueprint(dashboard_bp)

# Função para conectar ao banco usando pyodbc
def conectar(retries=3, delay=2):
    for tentativa in range(1, retries + 1):
        try:
            print(f"🔄 Tentando conexão ao banco... tentativa {tentativa}")
            conn = pyodbc.connect(
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={os.getenv('DB_SERVER')};"
                f"DATABASE={os.getenv('DB_NAME')};"
                f"UID={os.getenv('DB_USER')};"
                f"PWD={os.getenv('DB_PASSWORD')};"
                "Encrypt=yes;"
                "TrustServerCertificate=yes;"
                "Connection Timeout=30;"
            )
            print("✅ Conexão com o banco estabelecida com sucesso!")
            return conn
        except Exception as e:
            print(f"⚠️ Erro na tentativa {tentativa}: {e}")
            if tentativa < retries:
                print(f"⏳ Aguardando {delay} segundos para nova tentativa...")
                time.sleep(delay)
            else:
                print("❌ Todas as tentativas de conexão falharam.")
                return None

# Conecta ao banco de dados
conn = conectar()

@app.route('/')
def home():
    return jsonify({"mensagem": "API da Rifa está rodando com sucesso!"})

@app.route('/numeros')
def listar_numeros():
    if conn is None:
        return jsonify({"erro": "Sem conexão com o banco"}), 500
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Numero, ISNULL(P.Nome, '') AS NomeParticipante
        FROM NumerosRifa NR
        LEFT JOIN Participantes P ON NR.IdParticipante = P.Id
        ORDER BY Numero
    """)
    resultados = cursor.fetchall()
    numeros = [{"numero": row[0], "participante": row[1]} for row in resultados]
    return jsonify(numeros)

@app.route('/front')
def front():
    return send_from_directory('static', 'index.html')

@app.route('/comprar', methods=['POST'])
def comprar_numero():
    if conn is None:
        return jsonify({"mensagem": "Sem conexão com o banco", "success": False}), 500

    dados = request.get_json()
    numero = dados.get('numero')
    nome_participante = dados.get('participante')

    if not numero or not nome_participante:
        return jsonify({"mensagem": "Dados incompletos.", "success": False}), 400

    nome_participante = nome_participante.strip()
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Participantes WHERE LOWER(Nome) = LOWER(?)", (nome_participante,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"mensagem": "Participante não encontrado.", "success": False}), 404

    id_participante = row[0]

    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante = ?", (id_participante,))
    qtd_numeros = cursor.fetchone()[0]
    if qtd_numeros >= 4:
        return jsonify({"mensagem": "Você já comprou 4 números. Limite atingido!", "success": False}), 403

    cursor.execute("SELECT IdParticipante FROM NumerosRifa WHERE Numero = ?", (numero,))
    checar = cursor.fetchone()
    if checar and checar[0] is not None:
        return jsonify({"mensagem": f"Número {numero} já foi comprado!", "success": False}), 400

    cursor.execute(
        "UPDATE NumerosRifa SET IdParticipante = ?, DataCompra = GETDATE() WHERE Numero = ?",
        (id_participante, numero)
    )
    conn.commit()

    return jsonify({"mensagem": f"Número {numero} comprado com sucesso por {nome_participante}!", "success": True})

@app.route('/registrar', methods=['POST'])
def registrar():
    if conn is None:
        return jsonify({"mensagem": "Sem conexão com o banco", "success": False}), 500

    try:
        dados = request.get_json()
        nome = dados.get('nome')
        senha = dados.get('senha')

        if not nome or not senha:
            return jsonify({"mensagem": "Preencha nome e senha.", "success": False}), 400

        nome = nome.strip()
        cursor = conn.cursor()

        cursor.execute("SELECT Id FROM Participantes WHERE LOWER(Nome) = LOWER(?)", (nome,))
        if cursor.fetchone():
            return jsonify({"mensagem": "Este nome já está em uso. Escolha outro.", "success": False}), 409

        cursor.execute("SELECT ISNULL(MAX(Id), 0) + 1 FROM Participantes")
        next_id = cursor.fetchone()[0]

        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cursor.execute(
            "INSERT INTO Participantes (Id, Nome, SenhaHash) VALUES (?, ?, ?)",
            (next_id, nome, senha_hash)
        )
        conn.commit()

        return jsonify({"mensagem": f"Cadastro realizado com sucesso para {nome}!", "success": True})

    except Exception as e:
        print("❌ Erro no registrar:", e)
        return jsonify({"mensagem": "Erro interno no servidor.", "success": False}), 500

@app.route('/api/login', methods=['POST'])
def login():
    if conn is None:
        return jsonify({"mensagem": "Sem conexão com o banco", "success": False}), 500

    try:
        dados = request.get_json()
        nome = dados.get('nome')
        senha = dados.get('senha')

        if not nome or not senha:
            return jsonify({"mensagem": "Preencha nome e senha.", "success": False}), 400

        cursor = conn.cursor()
        cursor.execute("SELECT SenhaHash FROM Participantes WHERE LOWER(Nome) = LOWER(?)", (nome,))
        resultado = cursor.fetchone()

        if not resultado:
            return jsonify({"mensagem": "Participante não encontrado.", "success": False}), 404

        senha_hash = resultado[0]

        if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
            return jsonify({"mensagem": "Login realizado com sucesso!", "success": True, "nome": nome})
        else:
            return jsonify({"mensagem": "Senha incorreta.", "success": False}), 401

    except Exception as e:
        print("❌ ERRO GERAL NO LOGIN:", e)
        return jsonify({"mensagem": "Erro interno no servidor.", "success": False}), 500

@app.route('/login')
def pagina_login():
    return send_from_directory('static', 'login.html')

@app.route('/register')
def pagina_register():
    return send_from_directory('static', 'register.html')

@app.route('/meus-numeros')
def pagina_meus_numeros():
    return send_from_directory('static', 'meus-numeros.html')

@app.route('/meus-numeros/<nome_participante>')
def ver_numeros_participante(nome_participante):
    if conn is None:
        return jsonify({"mensagem": "Sem conexão com o banco", "success": False}), 500

    cursor = conn.cursor()
    cursor.execute("""
        SELECT NR.Numero
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        WHERE LOWER(P.Nome) = LOWER(?)
        ORDER BY NR.Numero
    """, (nome_participante,))
    resultados = cursor.fetchall()
    numeros = [row[0] for row in resultados]
    return jsonify({"participante": nome_participante, "numeros": numeros})

@app.route('/debug-vars')
def debug_vars():
    return jsonify({
        "DB_SERVER": os.getenv('DB_SERVER'),
        "DB_USER": os.getenv('DB_USER'),
        "DB_PASSWORD": os.getenv('DB_PASSWORD'),
        "DB_NAME": os.getenv('DB_NAME')
    })


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)
