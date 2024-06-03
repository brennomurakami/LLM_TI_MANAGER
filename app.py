from flask import Flask
from flask_login import LoginManager
from backend.routes import login_routes, index_routes, cadastrar_routes
from backend.db import configure_db
from backend.user import Usuario
import os

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY')

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.get(int(user_id)) 

# Configuração do MySQL
configure_db(app)

# Definindo a página de login
login_manager.login_view = 'login'

# Importando rotas
app.register_blueprint(login_routes)
app.register_blueprint(index_routes)
app.register_blueprint(cadastrar_routes)

if __name__ == '__main__':
    app.run(debug=True)
