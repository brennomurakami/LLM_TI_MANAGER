from flask import render_template, request, jsonify, Blueprint
from dotenv import load_dotenv
from backend.gpt import client, assistant
from backend.file import *
from backend.file import verificar_e_atualizar_indice
from io import BytesIO
from backend.database.modelos import db, Conta, Conversa, HistoricoConversa

index_routes = Blueprint('index_routes', __name__)

@index_routes.route('/')
def index():
    return render_template('index.html')

@index_routes.route('/gerar-resposta', methods=['POST'])
def gerar_resposta():
    pergunta = request.form['pergunta']
    thread = request.form['thread']
    print('thread recebida:', thread)
    
    # Inicializa a variável de resposta
    resposta = None

    # Loop para processar a resposta até que não haja mais a solicitação por 'FUNCOES NECESSÁRIAS'
    while True:
        message = client.beta.threads.messages.create(
            thread_id=thread,
            role="user",
            content=pergunta
        )

        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread,
            assistant_id=assistant.id
        )

        if run.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=thread
            )
        else:
            print(run.status)
            break

        # Obtém a última mensagem
        ultima_mensagem = messages.data[0].content[0].text.value
        print(ultima_mensagem)

        if 'VECTOR121:' in ultima_mensagem:
                print('Consultando base de dados vetorizada')
                resultados_similares = procurar_similaridade(ultima_mensagem)
                pergunta = " ".join(resultados_similares)

        else:
            # Atribui a resposta diretamente caso não seja solicitado as funções necessárias
            resposta = ultima_mensagem
            break

    print(resposta)

    return jsonify({'resposta': resposta})

@index_routes.route('/salvar-card', methods=['POST'])
def salvar_card():
    data = request.json
    nome_card = data.get('nome_card')
    thread = client.beta.threads.create()
    # Crie um novo card no banco de dados
    novo_card = Conversa(nome_conversa = nome_card, thread = thread.id)
    db.session.add(novo_card)
    db.session.commit()

    # Retorne o ID do card na resposta
    return jsonify({'id_card': novo_card.idconversa}), 200

@index_routes.route('/cards', methods=['GET'])
def get_cards():
    cards = Conversa.query.all()  # Consulta todos os cards do banco de dados
    print("cards")
    print(cards)
    cards_data = [{'idconversa': card.idconversa, 'nome_conversa': card.nome_conversa} for card in cards]  # Formata os dados dos cards
    return jsonify(cards_data)  # Retorna os dados dos cards como JSON

@index_routes.route('/deletar-card', methods=['POST'])
def deletar_card():
    data = request.json
    card_id = data['card_id']

    # Remove o card do banco de dados
    print("id: ", card_id)
    card = Conversa.query.filter_by(idconversa=card_id).first()
    print("card encontrado:", card)
    if card:
         # Remove todas as entradas correspondentes na tabela HistoricoConversa
        HistoricoConversa.query.filter_by(idconversa=card_id).delete()
        db.session.delete(card)
        db.session.commit()
        return 'Card excluído com sucesso do banco de dados.'
    else:
        return 'Card não encontrado no banco de dados.', 404
    
@index_routes.route('/get-thread/<card_id>', methods=['GET'])
def get_thread(card_id):
    card = Conversa.query.filter_by(idconversa=card_id).first()
    if card:
        return jsonify({'thread': card.thread}), 200
    else:
        return 'Card não encontrado no banco de dados.', 404
    
@index_routes.route('/salvar-pergunta', methods=['POST'])
def salvar_pergunta():
    data = request.json
    pergunta = data['pergunta']
    idconversa = data['idconversa']

    # Crie um novo registro na tabela historico_conversa
    nova_pergunta = HistoricoConversa(pergunta=pergunta, idconversa=idconversa)
    db.session.add(nova_pergunta)
    db.session.commit()

    return 'Pergunta salva com sucesso no banco de dados.', 200

@index_routes.route('/salvar-resposta', methods=['POST'])
def salvar_resposta():
    data = request.json
    resposta = data['resposta']
    idconversa = data['idconversa']

    # Crie um novo registro na tabela historico_conversa para a resposta
    nova_resposta = HistoricoConversa(resposta=resposta, idconversa=idconversa)
    db.session.add(nova_resposta)
    db.session.commit()

    return 'Resposta salva com sucesso no banco de dados.', 200

@index_routes.route('/mensagens/<card_id>', methods=['GET'])
def get_mensagens(card_id):
    historico = HistoricoConversa.query.filter_by(idconversa=card_id).order_by(HistoricoConversa.idhistorico).all()
     # Lista para armazenar as mensagens
    mensagens = []
    # Percorre cada elemento do histórico
    for mensagem in historico:
        # Verifica se é uma pergunta ou resposta e adiciona à lista de mensagens
        if mensagem.pergunta:
            mensagens.append({'tipo': 'pergunta', 'conteudo': mensagem.pergunta})
        elif mensagem.resposta:
            mensagens.append({'tipo': 'resposta', 'conteudo': mensagem.resposta})
    return jsonify(mensagens), 200

@index_routes.route('/alterar-nome-card', methods=['POST'])
def alterar_nome_card():
    data = request.json
    card_id = data['cardAlterar']
    novo_nome = data['novoNome']

    # Atualiza o nome do card no banco de dados
    card = Conversa.query.get(card_id)
    if card:
        card.nome_conversa = novo_nome
        db.session.commit()
        return 'Nome do card alterado com sucesso.', 200
    else:
        return 'Card não encontrado no banco de dados.', 404
    
@index_routes.route('/upload-arquivo', methods=['POST'])
def upload_arquivo():
    print("Função chamada")
    if 'file' not in request.files:
        return 'Nenhum arquivo enviado.', 400
    
    arquivo = request.files['file']

    if arquivo.filename == '':
        return 'Nenhum arquivo selecionado.', 400

    # Verifica se o arquivo é permitido
    if arquivo:
        print("Arquivo salvo com sucesso")

        # print(arquivo_texto)
        extensao = arquivo.filename.rsplit('.', 1)[-1].lower()

        file_stream = BytesIO(arquivo.read())
        verificar_e_atualizar_indice(file_stream, extensao)
        print("Arquivo salvo no banco vetorizado")
        
        return 'Arquivo enviado com sucesso.', 200
    else:
        return 'Tipo de arquivo não permitido.', 400