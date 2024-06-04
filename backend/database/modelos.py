from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Conta(db.Model, UserMixin):
    idconta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(45), nullable=False)
    senha = db.Column(db.String(100), nullable=False)

    # Flask-Login requires the following methods and properties:
    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.idconta)

class Conversa(db.Model):
    idconversa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome_conversa = db.Column(db.String(45), nullable=False)
    thread = db.Column(db.Text, nullable=True)
    idconta = db.Column(db.Integer, db.ForeignKey('conta.idconta'), nullable=True)
    conta = db.relationship('Conta', backref=db.backref('conversas', lazy=True))

class HistoricoConversa(db.Model):
    idhistorico = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resposta = db.Column(db.Text, nullable=True)
    pergunta = db.Column(db.Text, nullable=True)
    idconversa = db.Column(db.Integer, db.ForeignKey('conversa.idconversa'), nullable=False)
    conversa = db.relationship('Conversa', backref=db.backref('historico', lazy=True))

