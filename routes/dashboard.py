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

    cursor.execute("SELECT COUNT(*) FROM Participantes")
    total_participantes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NOT NULL")
    numeros_comprados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NULL")
    numeros_disponiveis = cursor.fetchone()[0]

    # Participantes com 4 números comprados
    cursor.execute('''
        SELECT P.Nome, COUNT(*) AS Quantidade
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        GROUP BY P.Nome
        HAVING COUNT(*) = 4
        ORDER BY P.Nome
    ''')
    top_raw = cursor.fetchall()
    top_participantes = [{"nome": nome, "quantidade": qtd} for nome, qtd in top_raw]

    # Participantes com pagamentos confirmados
    cursor.execute('''
        SELECT P.Nome, MAX(NR.DataCompra) AS UltimaCompra, COUNT(*) AS TotalPagos
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        WHERE NR.Pago = 1
        GROUP BY P.Nome
        ORDER BY UltimaCompra DESC
    ''')
    pagos_raw = cursor.fetchall()
    participantes_pagantes = [
        {
            "nome": nome,
            "ultima_compra": ultima.strftime('%d/%m/%Y %H:%M') if ultima else "",
            "total_pagos": total
        } for nome, ultima, total in pagos_raw
    ]

    return render_template(
        'dashboard.html',
        total_participantes=total_participantes,
        numeros_comprados=numeros_comprados,
        numeros_disponiveis=numeros_disponiveis,
        top_participantes=top_participantes,
        participantes_pagantes=participantes_pagantes  # ✅ AGORA ENVIAMOS A LISTA
    )
