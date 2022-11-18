import os
import hashlib
import zipfile
import requests
from bs4 import BeautifulSoup
import re

# 1. Программно разархивировать архив в выбранную директорию.
directory_to_extract_to = 'D:\\lab'  #директория извлечения файлов архива
arch_file = 'C:\\Users\\ADM\\Desktop\\3-6\\db_lab3\\tiff-4.2.0_lab1.zip' #путь к архиву
# открываем архив
test_zip = zipfile.ZipFile(arch_file)
# извлекаем все файлы из архива в директорию
test_zip.extractall(directory_to_extract_to)
#Завершение работы с архивом
test_zip.close()


# 2-1. Получить список файлов (полный путь) формата txt, находящихся в directory_to_extract_to.
# Сохранить полученный список в txt_files
txt_files = []
# используем os.walk чтобы просматривать каталог
# r - root; d - dirs; f - files
for r, d, f in os.walk(directory_to_extract_to):
    for file in f:
        if file.endswith(".txt"):
            txt_files.append(os.path.join(r, file))
test_file = open("D:\\lab\\test.txt", "w")
test_file.write(str(txt_files))
test_file.close()


# 2-2. Получить значения MD5 хеша для найденных файлов и вывести полученные данные на экран
for file in txt_files:
    target_file_data = open(file, 'rb').read()
    result = hashlib.md5(target_file_data).hexdigest()
    print(file, result)
#print()


# 3. Найти файл MD5 хеш которого равен target_hash в directory_to_extract_to
target_hash = "4636f9ae9fef12ebd56cd39586d33cfb"
target_file = '' #полный путь к искомому файлу
target_file_data = '' #содержимое искомого файла
for r, d, f in os.walk(directory_to_extract_to):
    for file in f:
        file_data = open(os.path.join(r, file), 'rb').read()
        if hashlib.md5(file_data).hexdigest() == target_hash:
            target_file = os.path.join(r, file)
            target_file_data = file_data
print(target_file)
print(target_file_data)
#print()


# 4. Ниже представлен фрагмент кода парсинга HTML страницы с помощью регулярных выражений
# для парсинга (сбора данных) HTML и XML документов, скрейпинга (получения веб-данных путем извлечения их со страниц веб-ресурсов) веб-страниц
# используется BeautifulSoup
bs_obj = BeautifulSoup(requests.get(target_file_data).text, "html.parser") #первый аргумент - html_doc и text-извлекает текст
# просматриваем и извлекаем ВСЕХ потомков тега, которые соответствуют переданным фильтрующим аргументам
rows = bs_obj.find_all('div', {"class": "Table-module_row__3TH83"})
# findChildren возвращает дочерние элементы этого объекта с заданным именем, берем 1 потомка
# recursive 	показывает, что нужно искать не только непосредственно в дочерних элементах узла, а во всем поддереве. По умолчанию – false (только в дочерних).
# удалили из таблицы заболели, умерли, вакцинировались и записали это в переменную и остались страны со статистикой по з/у/в
titles = rows.pop(0).findChildren(recursive=False)[1:]
for i in range(len(titles)): # привели к виду заболели, умерли, вакцинировались
    # Ищет шаблон в строке и заменяет его на указанную подстроку. Если шаблон не найден, строка остается неизменной.
    titles[i] = re.sub(r'[^А-Яа-я]+', '', str(titles[i]))
result_dct = {}  # словарь для записи содержимого таблицы
country_name = ''
for row in rows:
    # идем для каждой страны
    children = row.findChildren(recursive=False)  # нaходим остальнах потомков (только в дочерних и идем по странам)
    country_name = re.sub(r'[^А-Яа-я-\s]+', '', str(children.pop(0).text)).strip()  # strip - удаляет начальные и конечные пробелы из строки
    result_dct[country_name] = country_name
    result_dct[country_name] = {}  # словарь для записи потомков
    # потомки - данные по заболели, умерли и вакцинировались
    for index, child in enumerate(children): #enumerate — счетчик элементов последовательности в циклах
        value_cont = re.sub(r'[^0-9.%]+', '', str(child.text.split('(').pop(0)))  # split-сканирует всю строку и разделяет ее в случае нахождения разделителя
        result_dct[country_name][titles[index]] = value_cont if value_cont != '' else -1
print(result_dct)


# 5. Запись данных из полученного словаря в файл
#функция writer() создаст объект, подходящий для записи.
# Чтобы перебрать данные по строкам, используем функцию writerow()
titles = 'Страна;' + ';'.join(result_dct[next(iter(result_dct))].keys())
with open('lab.csv', 'w') as output:
    output.write(titles + '\n')
    for country in result_dct:
        output.write(country + ';')
        for col in result_dct[country]:
            output.write(str(result_dct[country][col]) + ';')
            if list(result_dct[country].keys())[-1] != col:
                output.write(';')
        if list(result_dct.keys())[-1] != country:
            output.write('\n')
output.close()


# 6. Вывод данных на экран для указанного первичного ключа (первый столбец таблицы)
target_country = input("Введите название страны: ")
country_data = []
with open('lab.csv') as file:
    lines = file.readlines()[1:]
    for line in lines:
        country_data = line.replace('\n', '').split(';')
        if country_data[0] == target_country:
            print(country_data[1:])

