from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///keyskillsorm.db')
base = declarative_base(bind=engine)
Session = sessionmaker()


class Queries(base):
    __tablename__ = 'queries'
    id = Column(Integer, primary_key=True)
    region_id = Column(Integer)
    query = Column(String, index=True)
    # __table_args__ = (Index('query_region_id_idx', 'query', 'skill_id'),)  # может быть только одна пара запрос-регион


class Regions(base):
    __tablename__ = 'regions'
    id = Column(Integer, primary_key=True)
    hh_region_id = Column(Integer, unique=True)
    region = Column(String, unique=True, index=True)

    def __str__(self):
        return f'id: {self.id}, hh_region_id: {self.hh_region_id}, region: {self.region}'


class Skills(base):
    __tablename__ = 'skills'
    id = Column(Integer, primary_key=True)
    skills = Column(String, unique=True, index=True)


class SkillsArray(base):
    __tablename__ = 'skills_array'
    id = Column(Integer, primary_key=True)
    query_id = Column(Integer, ForeignKey('queries.id'))
    skill_id = Column(Integer, ForeignKey('skills.id'))
    amount = Column(Integer, default=0)


# Заполнение таблицы regions учебными данными
def fill_regions():
    items = [{'hh_region_id': 0, 'region': 'везде'},
             {'hh_region_id': 1, 'region': 'Москва'},
             {'hh_region_id': 2, 'region': 'Санкт-Петербург'},
             {'hh_region_id': 3, 'region': 'Екатеринбург'}]
    with Session() as session:
        for item in items:
            if not session.query(Regions).filter_by(hh_region_id=item['hh_region_id']).count():
                session.add(Regions(hh_region_id=item['hh_region_id'], region=item['region']))
        session.commit()


# Добавление запроса и ключевых навыков по данному запросу в базу
def put_query(query, region, skills_list):
    with Session() as session:

        # получаем id запроса из таблицы queries
        query_id = get_query_id(query, region)

        # добавляем навыки в таблицу skills, которых там ещё нет
        lst = list(map(lambda x: str(x['name']).lower(), skills_list))  # список навыков, которые нужно добавить
        result = session.query(Skills.skills).filter(Skills.skills.in_(tuple(lst))).all()
        result = list(map(lambda x: x[0], result))  # список навыков, которые уже есть в таблице skills
        new_skills = [item for item in lst if item not in result]  # список навыков, которых нет в таблице skills
        skills_to_add = list(map(lambda x: Skills(skills=x), new_skills))
        session.bulk_save_objects(skills_to_add)
        session.commit()

        # получаем id добавленных навыков
        skills_id = session.query(Skills.id).filter(Skills.skills.in_(tuple(lst))).all()
        skills_id = list(map(lambda x: x[0], skills_id))

        # добавляем связку навыков (табл. skills) и запросов (табл. queries), увеличиваем счётчик на 1
        for item in skills_id:
            if not session.query(SkillsArray).filter_by(query_id=query_id, skill_id=item).count():
                session.add(SkillsArray(query_id=query_id, skill_id=item))
            session.query(SkillsArray).filter_by(query_id=query_id, skill_id=item).\
                update({SkillsArray.amount: SkillsArray.amount + 1})

        session.commit()


# Удаление записей из массива навыков
def del_query_array(query, region):
    with Session() as session:
        query_id = get_query_id(query, region)
        session.query(SkillsArray).filter_by(query_id=query_id).delete()
        session.commit()


# Получение id запроса, если нет - добавление запроса в таблицу
def get_query_id(query, region, ins=True):
    with Session() as session:
        query_id = session.query(Queries).filter_by(query=query.lower(), region_id=region).one_or_none()

        if not query_id and not ins:
            session.close()
            return None

        if not query_id:
            q = Queries(query=query.lower(), region_id=region)
            session.add(q)
            session.commit()
            query_id = q.id
        else:
            query_id = query_id.id

    return query_id


# получение статистики по навыкам
def get_skills_stat(query, region):
    query_id = get_query_id(query, region, False)
    if not query_id:
        return []

    with Session() as session:

        # получаем сумму всех навыков
        amount = session.query(func.sum(SkillsArray.amount)).filter_by(query_id=query_id)
        print(query_id, amount)

        # получаем список навыков
        min_percent = 1
        query = session.query(Skills.skills, SkillsArray.amount * 100 / amount)
        query = query.filter(SkillsArray.query_id == query_id)
        query = query.filter(SkillsArray.skill_id == Skills.id)
        query = query.filter(SkillsArray.amount * 100 / amount > min_percent)
        query = query.order_by(SkillsArray.amount.desc())
        query = query.all()

    return query


base.metadata.create_all()
fill_regions()
