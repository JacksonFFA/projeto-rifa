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

    # Top participantes (4 números comprados)
    cursor.execute('''
        SELECT P.Nome, COUNT(*) AS Quantidade
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        GROUP BY P.Nome
        HAVING COUNT(*) = 4
        ORDER BY Quantidade DESC
    ''')
    top_participantes = [{"nome": nome, "quantidade": qtd} for nome, qtd in cursor.fetchall()]

    # Participantes com pagamento confirmado
    cursor.execute('''
        SELECT P.Nome, MAX(NR.DataCompra), COUNT(*) AS TotalPagos
        FROM NumerosRifa NR
        INNER JOIN Participantes P ON NR.IdParticipante = P.Id
        WHERE NR.Pago = 1
        GROUP BY P.Nome
        ORDER BY MAX(NR.DataCompra) DESC
    ''')
    pagamentos_confirmados = cursor.fetchall()
    lista_pagamentos = []
    for nome, ultima_compra, total_pagos in pagamentos_confirmados:
        porcentagem = int((total_pagos / 4) * 100)
        lista_pagamentos.append({
            "nome": nome,
            "data": ultima_compra.strftime("%d/%m/%Y") if ultima_compra else "-",
            "total": total_pagos,
            "porcentagem": porcentagem
        })

    return render_template(
        'dashboard.html',
        total_participantes=total_participantes,
        numeros_comprados=numeros_comprados,
        numeros_disponiveis=numeros_disponiveis,
        top_participantes=top_participantes,
        lista_pagamentos=lista_pagamentos
    )
