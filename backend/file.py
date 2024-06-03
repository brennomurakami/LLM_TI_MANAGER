from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Inicializa os embeddings da OpenAI
embeddings = OpenAIEmbeddings()

# Função para limpar o texto removendo espaços em branco extras
def limpar_texto(texto):
    return " ".join(texto.split())

# Função para processar o arquivo PDF e extrair o texto
def processar_pdf(arquivo):
    leitor = PdfReader(arquivo)
    texto_bruto = ''
    for pagina in leitor.pages:
        texto = pagina.extract_text()
        if texto:
            texto_bruto += texto
    
    divisor_texto = CharacterTextSplitter(
        separator='\n',
        chunk_size=1000,
        chunk_overlap=300,
        length_function=len
    )

    textos_divididos = divisor_texto.split_text(texto_bruto)
    return textos_divididos

# Função para criar os índices FAISS a partir dos textos extraídos do PDF
def criar_indices_faiss(arquivo):
    textos = processar_pdf(arquivo)
    # Cria o índice FAISS a partir dos textos e dos embeddings
    vetor_store = FAISS.from_texts(textos, embeddings)
    # Salva o índice em um arquivo
    vetor_store.save_local("faiss_index")
    return vetor_store

# Função para carregar os índices FAISS de um arquivo local
def carregar_indices_faiss():
    vetor_store = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    return vetor_store

# Função para adicionar novos textos ao índice existente
def adicionar_texto_ao_indice(vetor_store, arquivo):
    textos = processar_pdf(arquivo)
    metadados = [{} for _ in textos] 
    vetor_store.add_texts(textos, metadatas=metadados)
    # Salva o índice atualizado em um arquivo
    vetor_store.save_local("faiss_index")

# Função para verificar se o índice existe e atualizar ou criar conforme necessário
def verificar_e_atualizar_indice(arquivo):
    caminho_indice = os.path.join("faiss_index", "index.faiss")
    if os.path.exists(caminho_indice):
        vetor_store = carregar_indices_faiss()
        adicionar_texto_ao_indice(vetor_store, arquivo)
    else:
        vetor_store = criar_indices_faiss(arquivo)
    return vetor_store

# Função para procurar similaridade no índice FAISS
def procurar_similaridade(consulta):
    consulta = consulta.replace("VECTOR121:", "").strip()
    vetor_store = carregar_indices_faiss()
    # Realiza a busca de similaridade
    resultados = vetor_store.similarity_search(query=consulta, k=2)
    textos_resultados = [limpar_texto(doc.page_content) for doc in resultados]
    textos_resultados = ' '.join(textos_resultados)
    return textos_resultados