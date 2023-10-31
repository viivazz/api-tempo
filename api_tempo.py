from flask import Flask, redirect, request, render_template, session, url_for
import uuid
import sqlite3

import requests

app = Flask(__name__)
app.secret_key = 'chave_secreta'  # Chave secreta para sessão

# Função para gerar uma APIKey única
def generate_api_key():
    return str(uuid.uuid4())

# Função para criar a tabela de usuários no banco de dados (SQLite neste exemplo)
def create_user_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, api_key TEXT)''')
    conn.commit()
    conn.close()

# Rota para exibir o formulário de registro
@app.route('/')
def registration_form():
    return render_template('index.html')

# Rota para processar o registro
@app.route('/register', methods=['GET', 'POST'])
def register_user():
    username = request.form['username']

    if username:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        
        # Verifique se o nome de usuário já existe no banco de dados
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            conn.close()
            return 'Nome de usuário já existe. Escolha outro nome de usuário.'
        
        api_key = generate_api_key()
        cursor.execute("INSERT INTO users (username, api_key) VALUES (?, ?)", (username, api_key))
        conn.commit()
        conn.close()

        return f' <span style=" font-size: 24px;">Usuário registrado! APIKey:</span> <span style="font-weight: bold; font-size: 24px;">{api_key}</span>'


    
    else:
        return 'Nome de usuário inválido.' 
    
# Função para processar o login e configurar a sessão com duração mais longa por padrão
def process_login(username, api_key):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # Verifique se o nome de usuário e a APIKey correspondem
    cursor.execute("SELECT username, api_key FROM users WHERE username = ? AND api_key = ?", (username, api_key))
    user_data = cursor.fetchone()

    if user_data:
        
        session['api_key'] = api_key
     
        session.permanent = True  # Isso estenderá a duração da sessão

        
        return True
    else:
        return False





# Rota para exibir o formulário de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'api_key' in session:
        # Se o usuário já está autenticado, redirecioná-los diretamente para a página de pesquisa
        return redirect(url_for('api'))

    if request.method == 'POST':
        username = request.form['username']
        api_key = request.form['api_key']

        if username and api_key:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            # Verifique se o nome de usuário e a APIKey correspondem
            cursor.execute("SELECT username, api_key FROM users WHERE username = ? AND api_key = ?", (username, api_key))
            user_data = cursor.fetchone()

            if user_data:
                # Defina a chave de sessão para a APIKey
                session['api_key'] = api_key

                # O usuário está logado!
                return redirect(url_for('api'))
            else:
                return 'Credenciais inválidas. Tente novamente.'

    return render_template('login_form.html')
# Rota para o arquivo api.py (acessado após login bem-sucedido)
@app.route('/api')
def api():
    if 'api_key' in session:
        # Autenticado, podemos continuar com a consulta de clima
        cidade, estado, dados_clima, mensagem = None, None, None, None
        if 'dados_clima' in session:
            dados_clima = session['dados_clima']
            cidade = dados_clima.get('results', {}).get('city_name', '').split(',')[0]
            estado = dados_clima.get('results', {}).get('state')

        return render_template('consulta_cep_clima.html', cidade=cidade, estado=estado, dados_clima=dados_clima, mensagem=mensagem)
    else:
        # Não autenticado, redirecionar para a página de login
        return redirect(url_for('login'))

@app.route('/consultar_cep_clima', methods=['POST'])
def consultar_cep_clima():
    cep = request.form.get('cep')
    cidade, estado, mensagem = obter_cidade_estado(cep)

    if cidade and estado:
        # Obter dados do clima da API da HGBrasil
        api_key = '9ab86e18'  # Substitua pela sua chave de API da HGBrasil
        url_clima = f"https://api.hgbrasil.com/weather?key={api_key}&city_name={cidade},{estado}"
        
        try:
            response = requests.get(url_clima)
            if response.status_code == 200:
                dados_clima = response.json()
                session['dados_clima'] = dados_clima  # Armazena os novos dados na sessão
                return redirect(url_for('api'))  # Redirecione para a página de pesquisa
            else:
                return "Falha ao obter os dados do clima."
            
        except Exception as e:
            return f"Erro na solicitação da API: {str(e)}"
    else:
        return "CEP inválido ou informações ausentes."

def obter_cidade_estado(cep):
    url = f"https://viacep.com.br/ws/{cep}/json/"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()

            if 'localidade' in data and 'uf' in data:
                cidade = data['localidade']
                estado = data['uf']
                return cidade, estado, None
            else:
                return None, None, "CEP inválido ou informações ausentes."

        else:
            return None, None, "Falha na solicitação da API. Verifique o CEP e tente novamente."

    except Exception as e:
        return None, None, f"Erro na solicitação da API: {str(e)}"




    

if __name__ == '__main__':
    create_user_table()
    app.run(debug=True)
