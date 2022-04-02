import sqlalchemy

engine = sqlalchemy.create_engine('postgresql://my_user:123456@localhost:5432/kurs_adv_db')
conn = engine.connect()

conn.execute("""CREATE TABLE IF NOT EXISTS people (
            id serial PRIMARY KEY,
            name varchar(40) NOT NULL,
            bdate varchar(40) NOT NULL,
            sex integer NOT NULL,
            city varchar(40) NOT NULL,
            relation integer NOT NULL
            );"""
             )

conn.execute("""CREATE TABLE IF NOT EXISTS partner (
            id serial PRIMARY KEY,
            name varchar(40) NOT NULL,
            bdate varchar(40) NOT NULL,
            sex integer NOT NULL,
            city varchar(40) NOT NULL,
            relation integer NOT NULL,
            photo_one varchar(999),
            photo_two varchar(999),
            photo_three varchar(999)
            );"""
             )

conn.execute("""CREATE TABLE IF NOT EXISTS people_partner (
            id serial PRIMARY KEY,
            people_id integer NOT NULL REFERENCES people(id),
            partner_id integer NOT NULL REFERENCES partner(id)
            );"""
             )

conn.execute("""CREATE TABLE IF NOT EXISTS favourite (
            id serial PRIMARY KEY,
            people_id integer NOT NULL REFERENCES people(id),
            partner_id integer NOT NULL REFERENCES partner(id)
            );"""
             )

conn.execute("""CREATE TABLE IF NOT EXISTS blacklist (
            id serial PRIMARY KEY,
            people_id integer NOT NULL REFERENCES people(id),
            partner_id integer NOT NULL REFERENCES partner(id)
            );"""
             )


def insert_user_info(user_info_list):
    conn.execute(f"INSERT into people (name, bdate, sex, city, relation) values ({user_info_list});")
    return True


def insert_partner_info(user_info_id, partner_info_list):
    conn.execute(f"INSERT into partner (name, bdate, sex, city, relation, photo_one, photo_two, photo_three) "
                 f"VALUES ({partner_info_list});")
    last_index_partner = conn.execute(f"SELECT MAX(id) FROM partner;").fetchone()
    index_people = conn.execute(f"SELECT id FROM people WHERE name LIKE '%%{user_info_id}%%';").fetchone()
    conn.execute(f"INSERT into people_partner (people_id, partner_id) "
                 f"VALUES ('{index_people[0]}', '{last_index_partner[0]}');")
    return True


def duplicate_partner(people_id, partner_id):
    duplicate = conn.execute(f"""SELECT u.name = '{people_id}'  FROM partner p
                            JOIN people_partner pp ON p.id = pp.partner_id
                            JOIN people u ON pp.people_id = u.id
                            WHERE p.name LIKE '%%{partner_id}%%'
                            ;""").fetchone()
    if duplicate is None:
        return False
    return duplicate[0]


def duplicate_people(people_id):
    duplicate = conn.execute(f"""SELECT EXISTS 
                            (SELECT name FROM people
                            WHERE name LIKE '%%{people_id}%%')
                            ;""").fetchone()
    return duplicate[0]


def add_to_black_list(people_id, partner_id):
    index_people = conn.execute(f"SELECT id FROM people WHERE name LIKE '%%{people_id}%%';").fetchone()
    index_partner = conn.execute(f"SELECT id FROM partner WHERE name LIKE '%%{partner_id}%%';").fetchone()
    conn.execute(f"INSERT into blacklist (people_id, partner_id) "
                 f"VALUES ('{index_people[0]}', '{index_partner[0]}');")
    return True


def add_to_favourite_list(people_id, partner_id):
    index_people = conn.execute(f"SELECT id FROM people WHERE name LIKE '%%{people_id}%%';").fetchone()
    index_partner = conn.execute(f"SELECT id FROM partner WHERE name LIKE '%%{partner_id}%%';").fetchone()
    conn.execute(f"INSERT into favourite (people_id, partner_id) "
                 f"VALUES ('{index_people[0]}', '{index_partner[0]}');")
    return True


def black_list(people_id, partner_id):
    duplicate = conn.execute(f"""SELECT u.name = '{people_id}'  FROM partner p
                            JOIN blacklist b ON p.id = b.partner_id
                            JOIN people u ON b.people_id = u.id
                            WHERE p.name LIKE '%%{partner_id}%%'
                            ;""").fetchone()
    if duplicate is None:
        return False
    return duplicate[0]


def update_user_info(bdate):
    last_index_people = conn.execute(f"SELECT MAX(id) FROM people;").fetchall()
    conn.execute(f"UPDATE people SET bdate = '{bdate}' where id='{last_index_people[0][0]}';")
    return True
