import csv
import mysql.connector
import matplotlib.pyplot as plt
import datetime
from mysql.connector import Error
#%matplotlib inline
my_db = None

# ф-ия подсоединения к базе
def connect():
    global my_db
    try:
        my_db = mysql.connector.connect(user='root', password='lelido37', host='localhost', database='lab5')
        if my_db.is_connected():
            print('MySQL connecnted')
    except Error as e:
        print(e)

def fill_table(my_db, query):
    cursor = my_db.cursor()
    try:
        cursor.execute(query)
        my_db.commit()
        print('Query executed')
    except Error as e:
        print(e)

def summ_function(v_1, v_2):
    return [int(tmp_1) + int(tmp_2) for tmp_1, tmp_2 in zip(v_1, v_2)]

# получение списка зарегистрированных заражений по дням для конкретной страны
def transform_data(target, csv_file):
    dates_list = list()
    infected_list = list()
    with open(csv_file) as file_val:
        rows = list(csv.reader(file_val))
        titles = rows.pop(0)
        dates_list = titles[4:]
        for row in rows:
            if row[1] == target:
                if len(infected_list) == 0:
                    infected_list = row[4:]
                else:
                    infected_list = summ_function(infected_list, row[4:])
    return dates_list, infected_list

def create_tables():
    # таблица с информацией о стране
    query1 = '''
            CREATE TABLE IF NOT EXISTS `lab5`.`country_info` (
            `id` serial,
            `Country` varchar(255)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        '''
    # таблица с заражениями
    query2 = '''
            CREATE TABLE IF NOT EXISTS `lab5`.`country_stats` (
              `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
              `country_id` bigint(20) unsigned NOT NULL,
              `day` date DEFAULT NULL,
              `count_infected` float DEFAULT NULL,
              `Rt` float DEFAULT '0',
              UNIQUE KEY `id` (`id`),
              KEY `country_id` (`country_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        '''
    query3 = '''
            CREATE TABLE IF NOT EXISTS `lab5`.`graphs_stats` (
              `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
              `image` blob,
              `country_ids` json DEFAULT NULL,
              `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `id` (`id`)
            ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
        '''
    fill_table(my_db, query1)
    fill_table(my_db, query2)
    fill_table(my_db, query3)

def write_to_mysql(target, dates_list, infected_list):
    connect()
    # print(my_db)
    create_tables()
    cursor = my_db.cursor()
    country_id = 0
    row = None
    cursor.execute(f"SELECT * FROM `country_info` WHERE `Country` = '{target}'")
    row = cursor.fetchone()
    if row is None:
        cursor.execute(f'''INSERT INTO `country_info` (`Country`) VALUES ('{target}')''')
        country_id = cursor.lastrowid
    else:
        country_id = row[0]
    cursor.execute(f"SELECT * FROM `country_stats` WHERE `country_id` = {country_id} ")
    if len(cursor.fetchall()) > 0:
        return True
    for date, count in zip(dates_list, infected_list):
        date_list_split = date.split('/')
        formated_date = datetime.date(int('20' + date_list_split[2]), int(date_list_split[0]), int(date_list_split[1]))
        cursor.execute('''INSERT INTO `lab5`.`country_stats` (`country_id`, `day`, `count_infected`) 
                            VALUES (%s, %s, %s)''',
                       (country_id, formated_date, count))
    my_db.commit()


def get_rt_data(target):
    connect()
    cursor = my_db.cursor()
    # Rt рассчитывается как отношение числа новых выявленных заражений за последние четыре дня
    # к числу новых случаев за предыдущие четыре дня
    query = f'''
        UPDATE country_stats
        LEFT JOIN country_info ON (country_info.id = country_stats.country_id)
        JOIN (
        SELECT id, day, count_infected, 
            IFNULL((count_infected - (LAG(count_infected, 4) OVER (PARTITION BY country_id ORDER BY day))) / NULLIF(((LAG(count_infected, 4) OVER (PARTITION BY country_id ORDER BY day)) - (LAG(count_infected, 8) OVER (PARTITION BY country_id ORDER BY day))), 0), 0) AS Rt
        FROM country_stats) rt_stats ON rt_stats.id = country_stats.id
        SET country_stats.Rt = rt_stats.Rt
        WHERE country_info.`Country` = '{target}';
    '''
    cursor.execute(query)
    my_db.commit()


def plot_data(target):
    connect()
    cursor = my_db.cursor()
    country_id = 0
    query = f"SELECT `id` FROM `country_info` WHERE `Country` = '{target}'"
    cursor.execute(query)
    row = cursor.fetchone()
    if row is None:
        return False
    else:
        country_id = row[0]
    query = f'SELECT image FROM graphs_stats  WHERE country_ids = JSON_ARRAY({country_id});'
    cursor.execute(query)
    row = cursor.fetchone()
    if row is not None:
        return row[0]
    query = f'''
        SELECT `day`, `Rt`
        FROM country_stats
        WHERE country_stats.`country_id` = '{country_id}';
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    days = [row[0] for row in rows]
    rt = [row[1] for row in rows]
    #print(datetime.datetime.now())
    filename = str(target) + '.png'
    fig, ax = plt.subplots(nrows=1, ncols=1)
    ax.plot(days, rt)
    fig.savefig(filename)
    plt.close(fig)
    with open(filename, 'rb') as f:
        graph = f.read()
    query_update = f'''
        INSERT INTO `graphs_stats` (`image`, `country_ids`) VALUES (%s, %s);
    '''
    val = (graph, f'[{country_id}]')
    cursor.execute(query_update, val)
    my_db.commit()


def read_graph(countries):
    if len(countries) == 0:
        return False
    cursor = my_db.cursor()
    query = 'SELECT * FROM country_info WHERE '
    for country in countries:
        query += f"`Country` = '{country}' "
        if country != countries[-1]:
            query += ' OR '
    cursor.execute(query)
    rows = cursor.fetchall()
    country_ids = [str(row[0]) for row in rows]
    query = f"SELECT image FROM graphs_stats  WHERE country_ids = JSON_ARRAY({', '.join(country_ids)});"
    cursor.execute(query)
    row = cursor.fetchone()
    if row is None:
        return False
    with open(f"file{'_'.join(country_ids)}.png", 'wb') as f:
        f.write(row[0])


def plot_all(countries):
    cursor = my_db.cursor()
    query = f'''
    SELECT
        country_info.`id`,
        `Country`,
        `day`,
        `Rt`
    FROM
        country_stats
        LEFT JOIN country_info ON (country_info.id = country_stats.country_id)
    WHERE
        country_info.`Country` IN({', '.join([f"'{country}'" for country in countries])})
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    countries_dict = dict()
    for row in rows:
        if row[1] not in countries_dict:
            countries_dict[row[1]] = {'days': [], 'count_infected': []}
        countries_dict[row[1]]['days'].append(row[2])
        countries_dict[row[1]]['count_infected'].append(row[3])
    fig, ax = plt.subplots(nrows=1, ncols=1)
    for country in countries_dict:
        ax.plot(countries_dict[country]['days'], countries_dict[country]['count_infected'], label=country)
    ax.legend()
    plt.show()

if __name__ == '__main__':
    target_list = list()
    while True:
        target = input("Enter name country: ")
        if target == '':
            break
        target_list.append(target)
        # получили данные по странам
        dates_list, infected_list = transform_data(target, 'time_series_covid19_confirmed_global.csv')
        # подключились к БД, создали и заполнили таблицы
        write_to_mysql(target, dates_list, infected_list)
        # получение значений коэффициента Rt по дням, запись полученных данных в таблицу
        get_rt_data(target)
        # построение графика коэффициента распростронения вируса по дням с помощью модуля matplotlib для заданной страны,
        # запись полученного графика (в виде графического файла) в таблицу
        plot_data(target)
        # чтение графических данных из БД и запись их в файл
        read_graph([target])
    # построение графика коэффициента распространения вируса по дням для нескольких стран (один рисунок - несколько стран)
    plot_all(target_list)
    print()