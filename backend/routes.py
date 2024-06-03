from flask import Blueprint, request, jsonify, render_template
from flask_login import login_user, login_required, logout_user, current_user
from backend.file import *
from backend.db import mysql
from backend.gpt import client
from backend.user import Usuario
import os

login_routes = Blueprint('login_routes', __name__)
index_routes = Blueprint('index_routes', __name__)
cadastrar_routes = Blueprint('cadastrar_routes', __name__)

thread = ''
# Rota para fazer login
@login_routes.route('/login', methods=['POST'])
def login():
    dados = request.get_json()
    nome_usuario = dados.get('username')
    senha = dados.get('password')

    # Consulta ao banco de dados para verificar se o usuário e a senha estão corretos
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (nome_usuario, senha))
    dados_usuario = cursor.fetchone()
    cursor.close()

    if dados_usuario:
        usuario = Usuario(usuario_id=dados_usuario[0], nome_usuario=dados_usuario[1])
        login_user(usuario)
        return jsonify({'mensagem': 'Login realizado com sucesso!'})
    else:
        return jsonify({'mensagem': 'Nome de usuário ou senha incorretos!'}), 401
    
# Rota para cadastrar um usuário
@cadastrar_routes.route('/cadastrar', methods=['POST'])
def cadastrar():
    dados = request.get_json()
    nome_usuario = dados.get('username')
    senha = dados.get('password')

    # Consulta ao banco de dados para verificar se o usuário já existe
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s", (nome_usuario,))
    dados_usuario = cursor.fetchone()

    if dados_usuario:
        cursor.close()
        return jsonify({'erro': 'Nome de usuário já existe!'}), 400

    # Insere o novo usuário no banco de dados
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (nome_usuario, senha))
    mysql.connection.commit()
    cursor.close()

    return jsonify({'mensagem': 'Usuário cadastrado com sucesso!'})


# Rota do cadastro
@cadastrar_routes.route('/signup')
def cadastro():
    return render_template('signup.html')

# Rota Inicial
@index_routes.route('/')
def index():
    return render_template('login.html')

# Rota para fazer logout
@index_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('login.html')

# Rota da home
@index_routes.route('/home')
@login_required
def home():
    nome_usuario = current_user.nome_usuario   # Aqui, current_user é uma variável fornecida pelo Flask-Login
    print("nome:",nome_usuario)
    chats_usuario = Usuario.obter_chats_usuario()
    return render_template('index.html', username=nome_usuario, user_chats=chats_usuario)

# Criando rota para mandar a mensagem e receber a resposta
@index_routes.route('/get_response/<int:chat_id>', methods=['POST'])
@login_required
def get_response(chat_id):
    global thread
    data = request.get_json()
    mensagem_usuario = data.get('message')
    mensagem_inicial_usuario = mensagem_usuario
    while True:
        # Envia a mensagem do usuário para o servidor de chat
        client.beta.threads.messages.create(
            thread_id=thread,
            role="user",
            content=mensagem_usuario
        )

        # Obtém a resposta do servidor de chat
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread,
            assistant_id="asst_8dZmPoQiKTMkaxUjMuS6uUuc"
        )

        messages = client.beta.threads.messages.list(thread_id=thread)
        resposta_servidor = messages.data[0].content[0].text.value
        # Verifica se a resposta do servidor contém comandos especiais
        if "SQL121:" in resposta_servidor.upper():
            print('a')
        elif "VECTOR121:" in resposta_servidor.upper():
            print("entrou!")
            mensagem_usuario = procurar_similaridade(resposta_servidor)
        else:
            break

    # Salva a mensagem do usuário e a resposta do servidor no banco de dados
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO messages (text_usuario, text_servidor, chat_id) VALUES (%s, %s, %s)", (mensagem_inicial_usuario, resposta_servidor, chat_id))
    mysql.connection.commit()
    cursor.close()

    # Retorna a resposta ao usuário
    return jsonify({'message': resposta_servidor})

@index_routes.route('/add_chat', methods=['POST'])
@login_required
def add_chat():
    data = request.get_json()
    titulo = data.get('title')
    user_id = current_user.id
    global thread
    thread = client.beta.threads.create().id
    
    # Insere um novo chat no banco de dados
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO chats (title, user_id, id_gpt) VALUES (%s, %s, %s)", (titulo, user_id, thread))
    mysql.connection.commit()
    chat_id = cur.lastrowid
    cur.close()

    # Retorna os dados do chat recém-adicionado
    return jsonify({'chat_id': chat_id, 'title': titulo})

@index_routes.route('/get_messages/<int:chat_id>')
@login_required
def get_messages(chat_id):
    global thread
    # Consulta o banco de dados para obter as mensagens correspondentes ao chat_id
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM messages WHERE chat_id = %s", (chat_id,))
    messages = cur.fetchall()
    cur.close()
    
    # Formata as mensagens como uma lista de dicionários
    formatted_messages = [{"id": message[0], "usuario": message[1], "servidor": message[2]} for message in messages]
    
    # Obtém o ID GPT do chat
    cur = mysql.connection.cursor()
    cur.execute("SELECT id_gpt FROM chats WHERE id = %s", (chat_id,))
    thread = cur.fetchone()[0]
    cur.close()

    # Retorna as mensagens como resposta JSON
    return jsonify(formatted_messages)

@index_routes.route('/delete_chat/<int:chat_id>', methods=['POST'])
@login_required
def delete_chat(chat_id):
    try:
        # Deleta todas as mensagens associadas ao chat_id
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM messages WHERE chat_id = %s", (chat_id,))
        
        # Deleta o chat_id
        cur.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Chat deletado com sucesso."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@index_routes.route('/update_chat_title/<int:chat_id>', methods=['POST'])
@login_required
def update_chat_title(chat_id):
    try:
        data = request.get_json()
        novo_titulo = data.get('title')

        cur = mysql.connection.cursor()
        cur.execute("UPDATE chats SET title = %s WHERE id = %s", (novo_titulo, chat_id))
        mysql.connection.commit()
        cur.close()

        return jsonify({"message": "Título do chat atualizado com sucesso."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@index_routes.route('/upload-arquivo', methods=['POST'])
@login_required
def upload_arquivo():
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado.', 400

    arquivo = request.files['file']

    # Verifica se o usuário não selecionou nenhum arquivo
    if arquivo.filename == '':
        return 'Nenhum arquivo selecionado.', 400

    if arquivo:
        # Salva o arquivo na pasta uploads
        upload_folder = os.path.join("backend", 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        file_path = os.path.join(upload_folder, arquivo.filename)
        arquivo.save(file_path)
        
        # Cria e salva o vectorstore
        verificar_e_atualizar_indice(file_path)

        return 'Arquivo enviado e vetorizado com sucesso.', 200
    else:
        return 'Tipo de arquivo não permitido.', 400