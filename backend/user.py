from flask_login import UserMixin, current_user
from backend.db import mysql

class Usuario(UserMixin):
    def __init__(self, usuario_id, nome_usuario):
        self.id = usuario_id
        self.nome_usuario = nome_usuario

    @staticmethod
    def get(usuario_id):
        # Conecta-se ao banco de dados usando a instância do Flask-MySQLDB
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (usuario_id,))
        dados_usuario = cursor.fetchone()
        cursor.close()

        if dados_usuario:
            return Usuario(usuario_id=dados_usuario[0], nome_usuario=dados_usuario[1])
        else:
            return None

    @staticmethod
    def obter_chats_usuario():
        usuario_id = current_user.id
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM chats WHERE user_id = %s", (usuario_id,))
        chats = cursor.fetchall()
        cursor.close()
        return chats