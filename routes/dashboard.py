from flask import Blueprint, render_template
import pymssql
import os
from dotenv import load_dotenv

load_dotenv()

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
def dashboard():
    conn = pymssql.connect(
        server=os.getenv('DB_SERVER'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Participantes")
    total_participantes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NOT NULL")
    numeros_comprados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM NumerosRifa WHERE IdParticipante IS NULL")
    numeros_disponiveis = cursor.fetchone()[0]

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

    cursor.execute('''
        SELECT P.Nome, MAX(NR.DataPagamento), COUNT(*) AS TotalPagos
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        WHERE NR.Pago = 1
        GROUP BY P.Nome
        ORDER BY MAX(NR.DataPagamento) DESC
    ''')
    pagantes_raw = cursor.fetchall()
    participantes_pagantes = [
        {
            "nome": nome,
            "ultima_compra": data.strftime('%d/%m/%Y') if data else "—",
            "total_pagos": total,
            "valor_pago": f"{total * 25:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "porcentagem": int((total / 4) * 100)
        }
        for nome, data, total in pagantes_raw
    ]

    conn.close()
    return render_template(
        'dashboard.html',
        total_participantes=total_participantes,
        numeros_comprados=numeros_comprados,
        numeros_disponiveis=numeros_disponiveis,
        top_participantes=top_participantes,
        participantes_pagantes=participantes_pagantes
    )
