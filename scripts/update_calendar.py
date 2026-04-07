#!/usr/bin/env python3
# SR Dashboard - Kalender-Update via Google Apps Script
# Laedt alle Termine und aktualisiert die HTML-Datei.

import os, re, json, requests
from datetime import datetime

SHEETS_URL = os.environ.get('SHEETS_URL',
    'https://script.google.com/macros/s/AKfycbxpGj8Gdw9tT_gZNc8EsOqNuNQN6RhvboNCN_ru9RwMimjOWQWL-Q7igHB7RHfmMaTj/exec')
HTML_FILE = 'supplement-dashboard-schiedsrichter.html'

MONTHS_DE = ['Jan','Feb','Maer','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez']
WDAYS_DE  = ['So','Mo','Di','Mi','Do','Fr','Sa']

LOC_SVG = ('<svg width="11" height="11" viewBox="0 0 16 16" fill="none">'
           '<path d="M8 1.5C5.5 1.5 3.5 3.5 3.5 6c0 3.5 4.5 8.5 4.5 8.5s'
           '4.5-5 4.5-8.5c0-2.5-2-4.5-4.5-4.5z" stroke="currentColor" '
           'stroke-width="1.5" fill="none"/>'
           '<circle cx="8" cy="6" r="1.5" fill="currentColor"/></svg>')


def fetch_events():
    url = SHEETS_URL + '?action=calendar'
    print('  Rufe ' + url + ' auf...')
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise SystemExit('Apps Script Fehler: ' + str(data.get('error')))
    return data['events']


def get_weekday(ds):
    d = datetime.strptime(ds, '%Y-%m-%d')
    return WDAYS_DE[d.isoweekday() % 7]


def build_kal_cards(events):
    cards = ''
    game_idx = 0
    for e in events:
        d     = datetime.strptime(e['date'], '%Y-%m-%d')
        day   = d.day
        month = MONTHS_DE[d.month - 1]
        wd    = get_weekday(e['date'])
        typ   = e['type']
        t     = e.get('time', '')
        te    = e.get('end', '')
        title = e.get('title', '')
        addr  = e.get('addr', '')
        venue = e.get('venue', '')

        if typ == 'spiel':
            loc_html = ''
            if addr:
                loc_html = ('<span class="kal-detail-item">' + LOC_SVG +
                            '<span class="kal-location">' + venue +
                            ' &middot; ' + addr + '</span></span>')
            cards += (
                '\n      <div class="kal-card" data-type="spiel"'
                ' data-date="' + e['date'] + '" data-idx="' + str(game_idx) + '">'
                '<div class="kal-date-col"><div class="kal-day">' + str(day).zfill(2) + '</div>'
                '<div class="kal-month">' + month + '</div>'
                '<div class="kal-weekday">' + wd + '</div></div>'
                '<div class="kal-info"><div class="kal-title">' + title + '</div>'
                '<div class="kal-details"><span class="kal-time">' + t + ' &ndash; ' + te + '</span> ' + loc_html + '</div></div>'
                '<span class="kal-badge kb-spiel">Spiel</span>'
                '</div>'
            )
            game_idx += 1

        elif typ == 'training':
            cards += (
                '\n      <div class="kal-card" data-type="training"'
                ' data-date="' + e['date'] + '">'
                '<div class="kal-date-col"><div class="kal-day">' + str(day).zfill(2) + '</div>'
                '<div class="kal-month">' + month + '</div>'
                '<div class="kal-weekday">' + wd + '</div></div>'
                '<div class="kal-info"><div class="kal-title">SR Training</div>'
                '<div class="kal-details"><span class="kal-time">' + t + ' &ndash; ' + te + ' Uhr</span></div></div>'
                '<span class="kal-badge kb-training">Training</span>'
                '</div>'
            )

        elif typ == 'schulung':
            cards += (
                '\n      <div class="kal-card" data-type="schulung"'
                ' data-date="' + e['date'] + '">'
                '<div class="kal-date-col"><div class="kal-day">' + str(day).zfill(2) + '</div>'
                '<div class="kal-month">' + month + '</div>'
                '<div class="kal-weekday">' + wd + '</div></div>'
                '<div class="kal-info"><div class="kal-title">Schulung</div>'
                '<div class="kal-details"><span class="kal-time">' + t + ' &ndash; ' + te + ' Uhr</span></div></div>'
                '<span class="kal-badge kb-schulung">Schulung</span>'
                '</div>'
            )

    return cards


def build_games_js(events):
    spiele = [e for e in events if e['type'] == 'spiel']
    rows = []
    for g in spiele:
        rows.append('    ' + json.dumps([
            g['date'], g['title'], g.get('time',''),
            g.get('addr',''), g.get('venue',''), g.get('surface','')
        ], ensure_ascii=False))
    games_js  = 'var GAMES = [\n' + ',\n'.join(rows) + '\n  ];'
    dates_js  = 'var GAMES_DATES = ' + json.dumps([g['date'] for g in spiele]) + ';'
    return games_js, dates_js


def update_html(events):
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    spiele    = sum(1 for e in events if e['type'] == 'spiel')
    training  = sum(1 for e in events if e['type'] == 'training')
    schulung  = sum(1 for e in events if e['type'] == 'schulung')

    # Replace kal-list
    new_cards    = build_kal_cards(events)
    new_kal_list = '<div class="kal-list" id="kal-list">' + new_cards + '\n      </div>'
    content = re.sub(
        r'<div class="kal-list" id="kal-list">.*?</div>(?=\s*\n\s*</div>)',
        new_kal_list, content, flags=re.DOTALL, count=1)

    # Replace GAMES arrays
    games_js, dates_js = build_games_js(events)
    content = re.sub(r'var GAMES = \[.*?\];',      games_js,  content, flags=re.DOTALL, count=1)
    content = re.sub(r'var GAMES_DATES = \[.*?\];', dates_js,  content, count=1)

    # Ensure SHEETS_URL
    if SHEETS_URL and "var SHEETS_URL = '';" in content:
        content = content.replace("var SHEETS_URL = '';",
                                  "var SHEETS_URL = '" + SHEETS_URL + "';")

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    today = datetime.now().strftime('%d.%m.%Y')
    print('OK ' + HTML_FILE + ' aktualisiert: ' +
          str(spiele) + ' Spiele, ' +
          str(training) + ' Trainings, ' +
          str(schulung) + ' Schulungen (' + today + ')')


if __name__ == '__main__':
    print('Lade Termine vom Apps Script...')
    events = fetch_events()
    print('  ' + str(len(events)) + ' Termine geladen')
    update_html(events)
