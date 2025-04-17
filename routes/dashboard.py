from flask import Blueprint, jsonify
import pymssql
import os
from dotenv import load_dotenv

load_dotenv()

# Blueprint para a dashboard admin
dashboard_bp = Blueprint('dashboard', __name__)

# Conexão com banco de dados
conn = pymssql.connect(
    server=os.getenv('DB_SERVER'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

@dashboard_bp.route('/dashboard')
def dashboard():
    cursor = conn.cursor()

    # Quantidade total de participantes
    cursor.execute("SELECT COUNT(*) FROM Participantes")
    total_participantes = cursor.fetchone()[0]

    # Quantidade total de números comprados
    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NOT NULL")
    numeros_comprados = cursor.fetchone()[0]

    # Número total de números disponíveis
    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NULL")
    numeros_disponiveis = cursor.fetchone()[0]

    # Top 5 participantes por quantidade de números comprados
    cursor.execute('''
        SELECT TOP 5 P.Nome, COUNT(*) AS Quantidade
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        GROUP BY P.Nome
        ORDER BY Quantidade DESC
    ''')
    top_participantes = cursor.fetchall()

    return jsonify({
        "total_participantes": total_participantes,
        "numeros_comprados": numeros_comprados,
        "numeros_disponiveis": numeros_disponiveis,
        "top_participantes": [
            {"nome": nome, "quantidade": qtd} for nome, qtd in top_participantes
        ]
    })
