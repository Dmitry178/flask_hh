import sqlite3


class SQL:
    def __init__(self):
        self.conn = None
        self.curs = None

    def connect(self):
        if not self.conn:
            self.conn = sqlite3.connect('keyskills.db', check_same_thread=False)
        if not self.curs:
            self.curs = self.conn.cursor()

    # Добавление запроса и ключевых навыков по данному запросу в базу
    def put_query(self, query, region, skills_list):
        # TODO: добавить try/except
        self.connect()

        # получаем id запроса из таблицы queries
        query_id = self.get_query_id(query, region)

        # добавляем навыки в таблицу skills
        lst = list(map(lambda x: ((str(x['name']).lower()),), skills_list))
        self.curs.executemany('INSERT OR IGNORE INTO skills (skill) VALUES(?)', lst)

        # добавляем связку навыков (табл. skills) и запросов (табл. queries)
        lst = list(map(lambda x: '\'' + str(x['name']).lower() + '\'', skills_list))
        self.curs.execute(f"""
INSERT OR IGNORE INTO skills_array (query_id, skill_id)
SELECT {query_id}, id FROM skills WHERE skill IN ({', '.join(lst)})
""")

        # получаем id добавленных навыков
        lst = list(map(lambda x: str(x['name']).lower(), skills_list))
        self.curs.execute(f"SELECT id FROM skills WHERE skill IN ({','.join(['?'] * len(lst))})", lst)
        skills_id = list(map(lambda x: str(x[0]), self.curs.fetchall()))

        # увеличиваем счётчик навыков на 1
        if skills_id:
            self.curs.execute(f"""
UPDATE skills_array
SET amount = amount + 1
WHERE query_id = {query_id} AND skill_id IN ({', '.join(skills_id)})
        """)
        self.conn.commit()

    # Удаление записей из массива навыков
    def del_query_array(self, query, region):
        self.connect()
        query_id = self.get_query_id(query, region)
        self.curs.execute('DELETE FROM skills_array WHERE query_id = ?', str(query_id))

    # Получение id запроса, если нет - добавление запроса в таблицу
    def get_query_id(self, query, region, ins=True):
        # TODO: добавить try/except
        self.connect()
        self.curs.execute('SELECT id FROM queries WHERE query = ? AND region_id = ?', (query.lower(), region))
        query_id = self.curs.fetchall()
        if not query_id and not ins:
            return None
        if not query_id:
            self.curs.execute('INSERT INTO queries (query, region_id) VALUES(?, ?)', (query.lower(), region))
            self.conn.commit()
            query_id = self.curs.lastrowid
        else:
            query_id = query_id[0][0]
        return query_id

    # получение статистики по навыкам
    def get_skills_stat(self, query, region):
        self.connect()
        query_id = self.get_query_id(query, region, False)
        if not query_id:
            return []

        # получаем сумму всех навыков
        self.curs.execute('SELECT COUNT(amount) FROM skills_array WHERE query_id = ?', str(query_id))
        amount = self.curs.fetchall()[0][0]

        # получаем список навыков
        min_percent = 3
        self.curs.execute("""
SELECT s.skill, sa.amount * 100 / ?
FROM skills_array sa, skills s
WHERE query_id = ? AND sa.skill_id = s.id AND sa.amount * 100 / ? > ? 
ORDER BY amount DESC
        """, [amount, query_id, amount, min_percent])

        return self.curs.fetchall()