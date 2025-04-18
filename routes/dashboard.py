from flask import Blueprint, render_template
import pymssql
import os
from dotenv import load_dotenv

load_dotenv()

dashboard_bp = Blueprint('dashboard', __name__)

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

    # Participantes com todas as compras (4 números)
    cursor.execute("""
        SELECT P.Nome, COUNT(*) AS Quantidade
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        GROUP BY P.Nome
        HAVING COUNT(*) = 4
    """)
    top_raw = cursor.fetchall()
    top_participantes = [{"nome": nome, "quantidade": qtd} for nome, qtd in top_raw]

    # Participantes com números pagos (com barra de energia)
    cursor.execute("""
        SELECT P.Nome, MAX(NR.DataCompra) AS UltimaCompra, COUNT(*) AS TotalPagos
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        WHERE NR.Pago = 1
        GROUP BY P.Nome
    """)
    pagamentos_raw = cursor.fetchall()
    participantes_pagantes = [
        {"nome": nome, "ultima_compra": ultima.strftime('%d/%m/%Y') if ultima else "-", "total_pagos": pagos}
        for nome, ultima, pagos in pagamentos_raw
    ]

    return render_template(
        'dashboard.html',
        total_participantes=total_participantes,
        numeros_comprados=numeros_comprados,
        numeros_disponiveis=numeros_disponiveis,
        top_participantes=top_participantes,
        participantes_pagantes=participantes_pagantes
    )
