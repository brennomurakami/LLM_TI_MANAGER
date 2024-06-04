const chatContainer = document.getElementById('chat-container');
const centralText = document.getElementById('central-content');

// Função para adicionar mensagem do usuário à interface
function addUserMessage(message) {
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'message user-message';
    userMessageDiv.innerHTML = `<p>${message}</p>`;
    chatContainer.appendChild(userMessageDiv);
    centralText.style.display = 'none';
}

// Função para adicionar mensagem da IA à interface
function addBotMessage(message) {
    const botMessageDiv = document.createElement('div');
    botMessageDiv.className = 'message bot-message';
    botMessageDiv.innerHTML = message;
    chatContainer.appendChild(botMessageDiv);
}

document.addEventListener('DOMContentLoaded', () => {

const userInput = document.getElementById('chat-input');
const toggleBtn = document.getElementById('toggle-btn');
const sidebar = document.getElementById('sidebar');
const enviarBtn = document.getElementById('send-btn');
enviarBtn.addEventListener('click', handleUserMessage);

// Função para lidar com a submissão da mensagem do usuário
async function handleUserMessage(event) {
    if (event.key === 'Enter' || event.target.id === 'send-btn') {
        const pergunta = userInput.value;
        if (pergunta == '') {
            console.log(threadAtual)
            console.log(cardAtual)
            return
        }
        if (threadAtual == null) {
            await NovoChatSelecionado()
            console.log("Criando")
        }
        setTimeout(function() {
        console.log("Adicionando mensagem")
        addUserMessage(pergunta);

        // Envia a pergunta para o servidor
        fetch('/gerar-resposta', {
            method: 'POST',
            headers: {
                 'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: 'pergunta=' + encodeURIComponent(pergunta) + '&thread=' + encodeURIComponent(threadAtual)
        })
        .then(response => response.json())
        .then(data => {
            let resposta = data.resposta;
            console.log("Resposta recebida.")
            resposta = marked.parse(resposta)
            addBotMessage(resposta);

            // Salva a pergunta na tabela historico_conversa
            fetch('/salvar-pergunta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ pergunta: pergunta, idconversa: cardAtual })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao salvar pergunta no servidor.');
                }
                console.log('Pergunta salva com sucesso no servidor.');
            })
            .catch(error => {
                console.error('Erro ao enviar pergunta para salvamento no servidor:', error);
            });

            // Salva a resposta na tabela historico_conversa
            fetch('/salvar-resposta', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ resposta: resposta, idconversa: cardAtual })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Erro ao salvar resposta no servidor.');
                }
                console.log('Resposta salva com sucesso no servidor.');
            })
            .catch(error => {
                console.error('Erro ao enviar resposta para salvamento no servidor:', error);
            });

        })
        .catch(error => console.error('Erro ao enviar pergunta:', error));
        }, 800);

        userInput.value = '';
    }
}

toggleBtn.addEventListener('click', () => {
    if (sidebar.style.left === '0px') {
        sidebar.style.left = '-250px'
        toggleBtn.style.marginLeft = '0'
        toggleBtn.style.width = '40px'
        toggleBtn.textContent = 'chevron_right'
    } else {
        toggleBtn.textContent = 'chevron_left'
        toggleBtn.style.width = '525px'
        sidebar.style.left = '0px'
    }
});

userInput.addEventListener('keypress', handleUserMessage);

});

const themeBtn = document.getElementById('theme-btn');
const chats = document.getElementById('chats');
const body = document.querySelector('body');
let threadAtual
let cardAtual
let cardAlterar
let modal = document.getElementById('modal');
let closeBtn = document.getElementsByClassName('close')[0];
let confirmarBtn = document.getElementById('confirmar-btn');

function mostrarModal() {
    modal.style.display = 'block';
}

closeBtn.onclick = function() {
    modal.style.display = 'none';
    cardAlterar = ''
    document.getElementById('novo-nome-input').value = '';
}

// Função para fechar o modal ao clicar fora dele
window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = 'none';
        cardAlterar = ''
    }
    document.getElementById('novo-nome-input').value = '';
}

confirmarBtn.onclick = function() {
    // Obtém o novo nome do card
    let novoNome = document.getElementById('novo-nome-input').value;
    
    // Envia o novo nome do card para o servidor Flask
    fetch('/alterar-nome-card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ cardAlterar: cardAlterar, novoNome: novoNome })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao alterar o nome do card.');
        }
        console.log('Nome do card alterado com sucesso.');
        // Fecha o modal após confirmar a alteração
        modal.style.display = 'none';

        // Limpa o campo do formulário onde você digitou o novo nome
        document.getElementById('novo-nome-input').value = '';

         // Atualiza o nome do card no DOM
        const cardElement = document.getElementById(cardAlterar); // Selecione o elemento do card pelo ID
        if (cardElement) {
            cardElement.querySelector('p').textContent = novoNome; // Atualize o conteúdo do elemento com o novo nome
        } else {
            console.error('Elemento do card não encontrado no DOM.');
        }

        cardAlterar = ''
    })
    .catch(error => {
        console.error('Erro ao alterar o nome do card:', error);
        // Aqui você pode exibir uma mensagem de erro ao usuário, se desejar
    });
}

function handleCardClick(cardId) {
    fetch('/get-thread/' + cardId)
    .then(response => response.json())
    .then(data => {
        threadAtual = data.thread;
        console.log("Thread atual atualizada:", threadAtual);

         chatContainer.innerHTML = '<br><br>';
         centralText.style.display = 'block';
        // Carrega as mensagens da conversa atual
         carregarMensagens(cardId);
    })
    .catch(error => console.error('Erro ao obter thread do servidor:', error));

    cardAtual = cardId
    console.log("Card Atual: ", cardAtual)
}

async function NovoChatSelecionado() {
    const result = criarCard(); // Chama criarCard() normalmente
    if (result instanceof Promise) {
        // Se criarCard() retornar uma Promise, retorne-a diretamente
        return result;
    } else {
        // Se criarCard() não retornar uma Promise, crie e retorne uma Promise resolvida
        return Promise.resolve();
    }
}

function carregarMensagens(cardId) {
    console.log("entrou")
    fetch('/mensagens/' + cardId)
    .then(response => response.json())
    .then(messages => {
        // messages.sort((a, b) => a.idhistorico - b.idhistorico);
        // Para cada mensagem retornada, adicione à interface
        console.log(messages)
        messages.forEach(message => {
            if (message.tipo === 'pergunta') {
                addUserMessage(message.conteudo);
            } else if (message.tipo === 'resposta') {
                addBotMessage(message.conteudo);
            }
        });
    })
    .catch(error => console.error('Erro ao carregar mensagens do servidor:', error));
}

function deletar(card){
    if (cardAtual == card.id) {
        console.log("IGUAL")
        threadAtual = null
        cardAtual = null
        chatContainer.innerHTML = '<br><br>';
        centralText.style.display = 'block';
    }
    let cardId = card.id;
    // Obtém o elemento pai do botão de delete, que é o card a ser removido
    var cardToRemove = card;
    
    // Obtém o elemento pai do card, que é o contêiner de chats
    var chats = cardToRemove.parentNode;
    
    // Remove o card do contêiner de chats
    chats.removeChild(cardToRemove);

    console.log("id do card:", cardId)

    // Envia o ID do card para o servidor Flask para exclusão
    fetch('/deletar-card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ card_id: cardId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao excluir card no servidor.');
        }
        console.log('Card excluído com sucesso no servidor.');
    })
    .catch(error => {
        console.error('Erro ao enviar ID do card para exclusão no servidor:', error);
    });
}

function alterar(card){
    cardAlterar = card.id;
    console.log(cardAlterar)
    mostrarModal();
}

async function criarCard() {
    let nomeCard = 'Novo chat';
    console.log("entrou")
    // Envia o nome do card para o servidor Flask e obtém o ID gerado
    fetch('/salvar-card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({nome_card: nomeCard })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao salvar card no servidor.');
        }
        // Converte a resposta em JSON
        return response.json();
    })
    .then(data => {
        // Obtém o ID gerado do card na resposta
        const idCard = data.id_card;

        // Cria o elemento HTML do card com o ID gerado
        const novoCard = document.createElement('div');
        novoCard.classList.add('card');
        novoCard.setAttribute('id', idCard); // Define o ID do card com o ID gerado
        novoCard.innerHTML = `
            <p>${nomeCard}</p>
            <div id="card-op">
                <span class="material-symbols-outlined" id="edit">edit</span>
                <span class="material-symbols-outlined" id="delete">delete</span>
            </div>
        `;

         // Adiciona evento de clique para o novoCard
         novoCard.onclick = function(event) {
            if (event.target.id === 'edit') {
                alterar(novoCard);
            } else if (event.target.id === 'delete') {
                deletar(novoCard);
            }
            else{
                handleCardClick(this.id)
            }
        };
        chats.appendChild(novoCard);
        handleCardClick(novoCard.id);

        console.log('ID do card enviado com sucesso para o servidor:', idCard);
        return Promise.resolve()
    })
    .catch(error => {
        console.error('Erro ao enviar nome do card para o servidor:', error);
        return Promise.reject()
    });
}

function carregarCards() {
    fetch('/cards')
        .then(response => response.json())
        .then(cards => {
            // Para cada card retornado, crie um novo elemento de card no DOM
            cards.forEach(card => {
                const novoCard = document.createElement('div');
                novoCard.classList.add('card');
                novoCard.setAttribute('id', card.idconversa); // Define o ID do card
                novoCard.innerHTML = `
                    <p>${card.nome_conversa}</p>
                    <div id="card-op">
                        <span class="material-symbols-outlined" id="edit">edit</span>
                        <span class="material-symbols-outlined" id="delete">delete</span>
                    </div>
                `;

                // Adiciona evento de clique para o novoCard
                novoCard.onclick = function(event) {
                    if (event.target.id === 'edit') {
                        alterar(novoCard);
                    } else if (event.target.id === 'delete') {
                        deletar(novoCard);
                    }
                    else{
                        handleCardClick(this.id)
                    }
                };

                chats.appendChild(novoCard);  // Adiciona o novo card ao contêiner de chats
            });
        })
        .catch(error => {
            console.error('Erro ao carregar cards do servidor:', error);
        });
}

document.addEventListener('DOMContentLoaded', carregarCards);

function toggleTheme() {
    // Verifica se a classe 'light-mode' está presente no body
    var isLightMode = body.classList.contains('light-mode');

    // Se estiver no modo claro, alterna para o modo escuro; caso contrário, alterna para o modo claro
    if (isLightMode) {
        body.classList.remove('light-mode');
        // Adicione a classe 'dark-mode' para ativar o modo escuro
        body.classList.add('dark-mode');
        themeBtn.textContent = 'light_mode'
    } else {
        // Remove a classe 'dark-mode' para desativar o modo escuro
        body.classList.remove('dark-mode');
        // Adicione a classe 'light-mode' para ativar o modo claro
        body.classList.add('light-mode');
        themeBtn.textContent = 'dark_mode'
    }
}

// Adiciona o evento de clique ao elemento 'file-span'
document.getElementById('file-span').addEventListener('click', function() {
    // Clica no elemento 'file-input' para abrir a caixa de diálogo de seleção de arquivo
    document.getElementById('file-input').click();
});

// Adiciona o evento de alteração ao elemento 'file-input' para lidar com a seleção do arquivo
document.getElementById('file-input').addEventListener('change', function(event) {
    const file = event.target.files[0];  // Obtém o arquivo selecionado

    // Crie um objeto FormData para enviar o arquivo
    const formData = new FormData();
    formData.append('file', file);

    // Envie o arquivo para o servidor Flask usando Fetch
    fetch('/upload-arquivo', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao enviar o arquivo.');
        }
        return response.text();
    })
    .then(data => {
        console.log(data); // Log da resposta do servidor
        // Faça qualquer outra coisa que você queira fazer após enviar o arquivo
    })
    .catch(error => {
        console.error('Erro:', error);
    });
});

document.getElementById("sair-btn").addEventListener("click", async function () {
    try {
      const response = await fetch("/logout", {
        method: "GET",
      });
  
      if (response.ok) {
        // Redireciona o usuário para a página de login ou outra página de sua escolha
        window.location.href = "/";  // Redireciona para a página de login
      } else {
        console.error("Erro ao fazer logout:", response.statusText);
      }
    } catch (error) {
      console.error("Erro ao fazer logout:", error);
    }
  });