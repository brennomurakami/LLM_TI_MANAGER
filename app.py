from flask import Flask, render_template, request, jsonify, send_file
import sys
import os
from dotenv import load_dotenv
from backend.database.modelos import db
from backend.routes import index_routes

# Adiciona o diretório raiz do projeto ao caminho de pesquisa de módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

database_url = os.getenv('DATABASE_URL')

app = Flask(__name__)

# Configurações do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(index_routes)

# Inicializa o banco de dados com o aplicativo Flask
db.init_app(app)

# Cria todas as tabelas do banco de dados
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)