from app import db

class Conta(db.Model):
    idconta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario = db.Column(db.String(45), nullable=False)
    senha = db.Column(db.String(45), nullable=False)

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

