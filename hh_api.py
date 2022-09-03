import requests
import re
from pprint import pprint


def get_request(data):
    query = data['query']
    page = data['page']
    region = int(data['region'])
    per_page = 10
    print('data', data)
    params = {
        'text': query,
        'per_page': per_page,
        'page': page
    }
    print(f"region {region}")
    if region:
        params['area'] = region
        print('set region', int(region))

    url = f'https://api.hh.ru/vacancies'

    response = requests.get(url, params=params).json()
    if 'items' not in response:
        pprint(response)
        return None, None, {}

    vac = {}
    for item in response['items']:
        s = ''
        s += f"<b>Работодатель:</b> {item['employer']['name']}" + '<br>'
        s += f"<b>Позиция:</b> {item['name']}" + '<br>'
        s += '<b>Требования:</b> ' + replace_highlight_text(item['snippet']['requirement']) + '<br>'
        s += '<b>Обязанности:</b> ' + replace_highlight_text(item['snippet']['responsibility'])
        vac[item['id']] = s

    return response['found'], response['pages'], vac


def get_vac(id_vac):
    url_vac_id = f'https://api.hh.ru/vacancies/{id_vac}?host=hh.ru'
    response = requests.get(url_vac_id).json()

    if 'errors' in response:
        return 'Ошибка номера вакансии'

    vac = []
    try:
        vac.append(f"<b>Работодатель:</b> {replace_highlight_text(response['employer']['name'])}")
        if response['address']:
            vac.append(f"<b>Адрес:</b> {replace_highlight_text(response['address']['raw'])}")
        vac.append(f"<b>Позиция:</b> {response['name']}")
        if response['description']:
            vac.append('<b>Описание:</b>')
            vac.append(html_to_text(response['description']))
        if response['salary']:
            vac.append(
                '<b>Зарплата:</b>' + ((' от ' + str(response['salary']['from'])) if response['salary']['from'] else '') + \
                ((' до ' + str(response['salary']['to'])) if response['salary']['to'] else '') + \
                ((' ' + str(response['salary']['currency'])) if response['salary']['currency'] else ''))
        if 'employment' in response:
            if response['employment']:
                vac.append(f"<b>Занятость:</b> {response['employment']['name']}")
        if 'schedule' in response:
            if response['schedule']:
                vac.append(f"<b>График:</b> {response['schedule']['name']}")
        if 'experience' in response:
            if response['experience']:
                vac.append(f"<b>Опыт работы:</b> {response['experience']['name']}")
        if 'key_skills' in response:
            if response['key_skills']:
                vac1 = ['<b>Ключевые навыки:</b>']
                for i in response['key_skills']:
                    vac1.append(f"- {i['name']}")
                vac.append('<br>'.join(vac1))
        if 'professional_roles' in response:
            if response['professional_roles']:
                vac1 = ['<b>Профессиональные роли:</b>']
                for i in response['professional_roles']:
                    vac1.append(f"- {i['name']}")
                vac.append('<br>'.join(vac1))
        if 'specializations' in response:
            if response['specializations']:
                vac1 = ['<b>Специализации:</b>']
                for i in response['specializations']:
                    vac1.append(f"- {i['name']}")
                vac.append('<br>'.join(vac1))
        if 'languages' in response:
            if response['languages']:
                vac1 = ['<b>Знание языков:</b>']
                for i in response['languages']:
                    vac1.append(f"- {i['name']}, уровень {i['level']['name']}")
                vac.append('<br>'.join(vac1))
        vac.append(response['alternate_url'])
    except Exception as ex:
        # вывод в сыром виде в консоль, если была ошибка в обработке
        pprint(response)
        print()
        print(ex)
        return None

    return vac


def replace_highlight_text(s):
    return str(s).replace('<highlighttext>', '').replace('</highlighttext>', ''). \
        replace('/', ' / ').replace('<', '&lt;').replace('>', '&gt;')


def html_to_text(html=''):
    result = html.replace('<p>', '').replace('<strong>', '').replace('</strong>', '').replace('</p>', '\n') \
        .replace('<ul>', '').replace('</ul>', '').replace('</li>', '\n').replace('<li>', '- ') \
        .replace('<em>', '● ').replace('</em>', '').replace('<br />', '\n').replace('<br/>', '\n') \
        .replace('<br>', '\n').replace('​', '\n').replace('/', ' / ').replace('<', '&lt;').replace('>', '&gt;')
    result = re.sub(' +', ' ', result)
    result = re.sub('\n+', '\n', result)
    return result
