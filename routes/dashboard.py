@dashboard_bp.route('/dashboard')
def dashboard():
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
        ORDER BY Quantidade DESC
        OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
    ''')
    top_raw = cursor.fetchall()

    # Transformando tuplas em dicionários
    top_participantes = [{"nome": nome, "quantidade": qtd} for nome, qtd in top_raw]

    return render_template('dashboard.html',
                        total_participantes=total_participantes,
                        numeros_comprados=numeros_comprados,
                        numeros_disponiveis=numeros_disponiveis,
                        top_participantes=top_participantes)
