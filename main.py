import hh_api
import sql
from flask import Flask, render_template, request, make_response, redirect, url_for

app = Flask(__name__)
hh_sql = sql.SQL()


@app.route("/")
def index_html():
    return render_template('index.html')


@app.route("/search/")
def search_html():
    query_data = get_cookies()
    resp = make_response(render_template('search.html', query=query_data['query'], region=query_data['region']))
    set_cookies(resp, query_data)
    return resp


@app.route("/results/", methods=['GET', 'POST'])
def results_html():
    query_data = {'found': 0, 'page': 0, 'pages': 0}
    if request.method == 'POST':
        query_data['query'] = request.form['search']
        query_data['region'] = request.form['region']
    else:
        query_data = get_cookies()
        if 'stat' in request.args:
            hh_api.get_skills(query_data['query'], query_data['region'], hh_sql)
        if 'next' in request.args:
            query_data['page'] = 0 if query_data['page'] + 1 >= query_data['pages'] else query_data['page'] + 1
        if 'prev' in request.args:
            query_data['page'] = query_data['pages'] - 1 if query_data['page'] - 1 < 0 else query_data['page'] - 1
        if 'page' in request.args:
            if request.args.get('page').isdigit():
                page = int(request.args.get('page'))
                if 0 < page <= query_data['pages']:
                    query_data['page'] = page - 1

    found, pages, vac = hh_api.get_request(query_data)
    if found:
        query_data['found'] = found
        query_data['pages'] = pages

    stat = hh_sql.get_skills_stat(query_data['query'], query_data['region'])
    resp = make_response(render_template('results.html', vac=vac, query_data=query_data,
                                         region=get_region(query_data['region']), stat=stat))
    set_cookies(resp, query_data)
    return resp


@app.route("/vac/")
def vac_html():
    vac = None
    if 'id' in request.args:
        vac = hh_api.get_vac(request.args.get('id'))
    return render_template('vac.html', vac=vac)


def get_region(region_num):
    dict_regions = {'0': 'везде', '1': 'Москва', '2': 'Санкт-Петербург', '3': 'Екатеринбург'}
    region_str = '?'
    if region_num in dict_regions:
        region_str = dict_regions[region_num]
    return region_str


def get_cookies():
    query_data = {'query': 'python', 'region': '0', 'found': 0, 'page': 0, 'pages': 0}
    for key in query_data:
        cookie = request.cookies.get(key)
        if cookie:
            query_data[key] = cookie
    if isinstance(query_data['found'], str):
        query_data['found'] = int(query_data['found'])
    if isinstance(query_data['page'], str):
        query_data['page'] = int(query_data['page'])
    if isinstance(query_data['pages'], str):
        query_data['pages'] = int(query_data['pages'])
    return query_data


def set_cookies(resp, query_data):
    for key, value in query_data.items():
        resp.set_cookie(key, str(value), 60 * 60 * 24 * 15)


if __name__ == '__main__':
    app.run(debug=True)
