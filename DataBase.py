import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()
db = 'postgresql://postgres:m20i11sha92@localhost:5432/VKinder'
engine = sq.create_engine(db)
Session = sessionmaker(bind=engine)
session = Session()


class MainUser(Base):
    __tablename__ = 'main_user'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    name = sq.Column(sq.String)
    age = sq.Column(sq.String)
    city = sq.Column(sq.String)
    relation = sq.Column(sq.String)
    couples = relationship('CoupleUser', back_populates='main_user')


class CoupleUser(Base):
    __tablename__ = 'couple_user'
    id = sq.Column(sq.Integer, primary_key=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    name = sq.Column(sq.String)
    id_main_user = sq.Column(sq.Integer, sq.ForeignKey('main_user.vk_id'))
    main_user = relationship(MainUser)


def create_tables():
    Base.metadata.create_all(engine)


def add_user(user):
    try:
        session.expire_on_commit = False
        session.add(user)
        session.commit()
    except:
        session.rollback()
        raise


def check_user():
    users = session.query(CoupleUser).all()
    users_list = [couple_id.vk_id for couple_id in users]
    return users_list
