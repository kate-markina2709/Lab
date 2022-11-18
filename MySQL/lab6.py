import random
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import func

def print_task(res):
    for row in res:
        print(row.__dict__)

db_host = "mysql+pymysql://root:lelido37@localhost"
def create_db(name):
    global db_host
    engine_host = sqlalchemy.create_engine(db_host)
    connect = engine_host.connect()
    connect.execute("commit")
    connect.execute(f"CREATE DATABASE IF NOT EXISTS {name}")
    connect.close()

db_name = 'lab6'
create_db(db_name)
engine = sqlalchemy.create_engine(f"{db_host}/{db_name}")
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Release(Base):
    __tablename__ = 'release'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    release_name = sqlalchemy.Column(sqlalchemy.String(255))
    release_date = sqlalchemy.Column(sqlalchemy.Date)
    info_musician = relationship('Musician', secondary='mus_release')

class Musician(Base):
    __tablename__ = 'musician'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name_artist = sqlalchemy.Column(sqlalchemy.String(255))
    birthday_artist = sqlalchemy.Column(sqlalchemy.Date)
    info_release = relationship('Release', secondary='mus_release')

class MusicianRelease(Base):
    __tablename__ = 'mus_release'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    musician_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('musician.id'))
    release_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('release.id'))

class Manager(Base):
    __tablename__ = 'manager'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String(255))
    phone = sqlalchemy.Column(sqlalchemy.String(20))
    musician_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('musician.id'))

class Contact(Base):
    __tablename__ = 'contact_info'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    city = sqlalchemy.Column(sqlalchemy.String(255))
    country = sqlalchemy.Column(sqlalchemy.String(255))
    phone = sqlalchemy.Column(sqlalchemy.String(20))
    musician_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('musician.id'))

Base.metadata.create_all(engine)

info_musician = [
    Musician(name_artist='Иванов Иван Иванович', birthday_artist='2000-02-02'),
    Musician(name_artist='Петров Петр Петрович', birthday_artist='1970-03-05'),
    Musician(name_artist='Михайлов Михаил Михайлович', birthday_artist='1990-10-19')
]

info_release = [
   Release(release_name='Первый', release_date='2022-03-15'),
   Release(release_name='Второй', release_date='2022-02-15'),
   Release(release_name='Третий', release_date='2022-01-01')
]

info_manager = [
    Manager(name='Романов Роман Романович', phone='8123'),
    Manager(name='Николаев Николай Николаевич', phone='8456'),
    Manager(name='Андреев Андрей Андреевич', phone='8789')
]

info_contact = [
    Contact(city='Город №1', country='Страна №1', phone='8111'),
    Contact(city='Город №2', country='Страна №2', phone='8222'),
    Contact(city='Город №3', country='Страна №3', phone='8333'),
    Contact(city='Город №4', country='Страна №4', phone='8444'),
    Contact(city='Город №5', country='Страна №5', phone='8555')
]

all_row = info_musician + info_release + info_manager + info_contact
session.add_all(all_row)

info_musician[0].info_release.append(info_release[2])
info_musician[0].info_release.append(info_release[1])
info_musician[2].info_release.append(info_release[0])
session.commit()

for contact_detail in info_contact:
    contact_detail.musician_id = random.choice(info_musician).id
session.commit()

musician_ids = []
for tmp_mus in info_musician:
    musician_ids.append(tmp_mus.id)
random.shuffle(musician_ids)
for manager in info_manager:
    if len(musician_ids):
        manager.musician_id = musician_ids.pop(0)
session.commit()

# Вывести все релизы, выпущенные после указанной даты
results = session.query(Release).filter(Release.release_date > '2022-02-10').all()
print_task(results)

# Вывести все релизы, в записи которых принимал участие заданный музыкант
results = session.query(Release) \
    .join(MusicianRelease, MusicianRelease.release_id == Release.id) \
    .join(Musician, Musician.id == MusicianRelease.musician_id) \
    .filter(Musician.id == 1) \
    .all()
print_task(results)

# Вывести всех музыкантов и их номера телефона, которые имеют несколько адресов проживания
results = session.query(Musician, func.count(Contact.musician_id)) \
    .join(Contact, Musician.id == Contact.musician_id) \
    .group_by(Musician.id) \
    .having(func.count(Contact.id) >= 2) \
    .with_entities(Musician.name_artist, func.group_concat(Contact.phone.distinct())) \
    .all()
print(results)

# Вывести список менеджеров, клиенты которых выпустили только один релиз
results = session.query(Manager) \
    .join(Musician, Manager.musician_id == Musician.id) \
    .join(MusicianRelease, Musician.id == MusicianRelease.musician_id) \
    .group_by(MusicianRelease.musician_id, Manager.id) \
    .having(func.count(MusicianRelease.musician_id) == 1) \
    .all()
print_task(results)

session.close()
