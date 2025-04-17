from flask import Blueprint, render_template, send_from_directory
import pymssql
import os
from dotenv import load_dotenv

load_dotenv()

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

    # Total de participantes
    cursor.execute("SELECT COUNT(*) FROM Participantes")
    total_participantes = cursor.fetchone()[0]

    # Total de números comprados
    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NOT NULL")
    numeros_comprados = cursor.fetchone()[0]

    # Total de números disponíveis
    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NULL")
    numeros_disponiveis = cursor.fetchone()[0]

    # Top participantes
    cursor.execute("""
        SELECT P.Nome, COUNT(*) AS Quantidade
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        GROUP BY P.Nome
        ORDER BY Quantidade DESC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
    """)
    top_participantes = cursor.fetchall()

    # Montar HTML direto da pasta static
    html_path = os.path.join(os.getcwd(), 'static', 'dashboard.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Substituir placeholders pelos dados
    html = html.replace('{{ total_participantes }}', str(total_participantes))
    html = html.replace('{{ numeros_comprados }}', str(numeros_comprados))
    html = html.replace('{{ numeros_disponiveis }}', str(numeros_disponiveis))

    top_lista = ''.join([f"<li>{nome}: <strong>{qtd}</strong> números</li>" for nome, qtd in top_participantes])
    html = html.replace('{{ top_participantes }}', top_lista)

    return html
