from flask import Blueprint, render_template
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

    # Top participantes
    cursor.execute('''
        SELECT P.Nome, COUNT(*) AS Quantidade
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        GROUP BY P.Nome
        ORDER BY Quantidade DESC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
    ''')
    top_raw = cursor.fetchall()
    top_participantes = [{"nome": nome, "quantidade": qtd} for nome, qtd in top_raw]

    # Participantes que já pagaram pelo menos 1 número
    cursor.execute('''
        SELECT 
            P.Nome,
            MAX(NR.DataCompra) AS UltimaCompra,
            COUNT(*) AS TotalPagos
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        WHERE NR.Pago = 1
        GROUP BY P.Nome
        ORDER BY P.Nome
    ''')
    participantes_pagantes_raw = cursor.fetchall()
    participantes_pagantes = [
        {
            "nome": nome,
            "ultima_compra": ultima_compra.strftime('%d/%m/%Y') if ultima_compra else '—',
            "total_pagos": total_pagos
        }
        for nome, ultima_compra, total_pagos in participantes_pagantes_raw
    ]

    return render_template(
        'dashboard.html',
        total_participantes=total_participantes,
        numeros_comprados=numeros_comprados,
        numeros_disponiveis=numeros_disponiveis,
        top_participantes=top_participantes,
        participantes_pagantes=participantes_pagantes
    )
