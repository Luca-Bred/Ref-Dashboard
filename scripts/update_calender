#!/usr/bin/env python3
"""
SR Dashboard – Kalender-Update via Google Apps Script
Ruft Termine direkt vom Apps Script ab (kein iCal-Link nötig).
"""

import os, re, json, requests
from datetime import datetime

SHEETS_URL = os.environ.get('SHEETS_URL',
    'https://script.google.com/macros/s/AKfycbxpGj8Gdw9tT_gZNc8EsOqNuNQN6RhvboNCN_ru9RwMimjOWQWL-Q7igHB7RHfmMaTj/exec')
HTML_FILE  = 'supplement-dashboard-schiedsrichter.html'

MONTHS_DE = ['Jan','Feb','Mär','Apr','Mai','Jun',
             'Jul','Aug','Sep','Okt','Nov','Dez']
WDAYS_DE  = ['So','Mo','Di','Mi','Do','Fr','Sa']


def fetch_events():
    """Termine vom Apps Script holen – kein iCal nötig."""
    url  = SHEETS_URL + '?action=calendar'
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get('ok'):
        raise SystemExit(f"Apps Script Fehler: {data.get('error')}")
    return data['events']


def build_kal_cards(events):
    cards    = ''
    game_idx = 0
    for e in events:
        d     = datetime.strptime(e['date'], '%Y-%m-%d')
        day   = d.day
        month = MONTHS_DE[d.month - 1]
        wd    = WDAYS_DE[d.weekday() + 1 if d.weekday() < 6 else 0]

        if e['type'] == 'spiel':
            loc_html = ''
            if e.get('addr'):
                loc_html = (
                    '<span class="kal-detail-item">'
                    '<svg width="11" height="11" viewBox="0 0 16 16" fill="none">'
                    '<path d="M8 1.5C5.5 1.5 3.5 3.5 3.5 6c0 3.5 4.5 8.5 4.5 8.5s'
                    '4.5-5 4.5-8.5c0-2.5-2-4.5-4.5-4.5z" stroke="currentColor" '
                    'stroke-width="1.5" fill="none"/>'
                    '<circle cx="8" cy="6" r="1.5" fill="currentColor"/></svg>'
                    f'<span class="kal-location">{e["venue"]} &middot; {e["addr"]}</span>'
                    '</span>'
                )
            cards += f'''
      <div class="kal-card" data-type="spiel" data-date="{e['date']}" data-idx="{game_idx}">
        <div class="kal-date-col"><div class="kal-day">{day:02d}</div><div class="kal-month">{month}</div><div class="kal-weekday">{wd}</div></div>
        <div class="kal-info"><div class="kal-title">{e['title']}</div><div class="kal-details"><span class="kal-time">{e['time']} &ndash; {e['end']}</span> {loc_html}</div></div>
        <span class="kal-badge kb-spiel">Spiel</span>
      </div>'''
            game_idx += 1
        else:
            cards += f'''
      <div class="kal-card" data-type="schulung" data-date="{e['date']}">
        <div class="kal-date-col"><div class="kal-day">{day:02d}</div><div class="kal-month">{month}</div><div class="kal-weekday">{wd}</div></div>
        <div class="kal-info"><div class="kal-title">Schulung</div><div class="kal-details"><span class="kal-time">{e['time']} &ndash; {e['end']} Uhr</span></div></div>
        <span class="kal-badge kb-schulung">Schulung</span>
      </div>'''
    return cards


def build_games_js(events):
    spiele = [e for e in events if e['type'] == 'spiel']
    rows   = ['    ' + json.dumps(
        [g['date'], g['title'], g['time'], g.get('addr',''), g.get('venue',''), g.get('surface','')],
        ensure_ascii=False) for g in spiele]
    games_js  = 'var GAMES = [\n' + ',\n'.join(rows) + '\n  ];'
    dates_js  = 'var GAMES_DATES = ' + json.dumps([g['date'] for g in spiele]) + ';'
    return games_js, dates_js


def update_html(events):
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    spiele    = sum(1 for e in events if e['type'] == 'spiel')
    schulungen = sum(1 for e in events if e['type'] == 'schulung')

    # kal-list ersetzen
    new_cards    = build_kal_cards(events)
    new_kal_list = f'<div class="kal-list" id="kal-list">{new_cards}\n      </div>'
    content = re.sub(
        r'<div class="kal-list" id="kal-list">.*?</div>(?=\s*\n\s*</div>)',
        new_kal_list, content, flags=re.DOTALL, count=1)

    # GAMES-Arrays ersetzen
    games_js, dates_js = build_games_js(events)
    content = re.sub(r'var GAMES = \[.*?\];',      games_js,  content, flags=re.DOTALL, count=1)
    content = re.sub(r'var GAMES_DATES = \[.*?\];', dates_js,  content, count=1)

    # SHEETS_URL sicherstellen
    if SHEETS_URL and "var SHEETS_URL = '';" in content:
        content = content.replace("var SHEETS_URL = '';",
                                  f"var SHEETS_URL = '{SHEETS_URL}';")

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    today = datetime.now().strftime('%d.%m.%Y')
    print(f'✓ {HTML_FILE} aktualisiert: {spiele} Spiele, {schulungen} Schulungen ({today})')


if __name__ == '__main__':
    print('Lade Termine vom Apps Script...')
    events = fetch_events()
    print(f'  {len(events)} Termine geladen')
    update_html(events)
