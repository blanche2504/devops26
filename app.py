# app.py — versione con database (ES06)
import os

from flask import Flask, jsonify, request
from sqlalchemy import String, create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

DATABASE_URL = os.environ["DATABASE_URL"]  # postgresql+psycopg://user:pw@db:5432/eventi

# pool_pre_ping: dopo un kill/start del db la connessione viene ricreata da sola
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


class Evento(Base):
    __tablename__ = "eventi"
    id: Mapped[int] = mapped_column(primary_key=True)
    titolo: Mapped[str] = mapped_column(String(200))

    def to_dict(self):
        return {"id": self.id, "titolo": self.titolo}


# Crea le tabelle all'avvio. Se il db non è pronto l'app si ferma: serve depends_on.
Base.metadata.create_all(engine)

app = Flask(__name__)


@app.errorhandler(OperationalError)
def db_non_raggiungibile(_e):
    return jsonify(errore="database non raggiungibile"), 503


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/version")
def version():
    return jsonify(version=os.environ.get("APP_VERSION", "dev"))


@app.get("/eventi")
def lista_eventi():
    with Session(engine) as s:
        return jsonify([e.to_dict() for e in s.scalars(select(Evento).order_by(Evento.id))])


@app.post("/eventi")
def crea_evento():
    dati = request.get_json(silent=True) or {}
    titolo = dati.get("titolo")
    if not titolo:
        return jsonify(errore="campo 'titolo' obbligatorio"), 400
    with Session(engine) as s:
        e = Evento(titolo=titolo)
        s.add(e)
        s.commit()
        return jsonify(e.to_dict()), 201
