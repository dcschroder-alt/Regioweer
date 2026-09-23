#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_KEY = os.environ.get('KNMI_EDR_API_KEY', '').strip()
if not API_KEY:
    raise SystemExit('KNMI_EDR_API_KEY ontbreekt')

BASE = ('https://api.dataplatform.knmi.nl/edr/v1/collections/'
        '10-minute-in-situ-meteorological-observations/locations/0-20000-0-06260')
now = datetime.now(timezone.utc)
start = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
params = {
    'datetime': f"{start.isoformat().replace('+00:00','Z')}/{now.isoformat().replace('+00:00','Z')}",
    'parameter-name': 'ta',
}
req = Request(BASE + '?' + urlencode(params), headers={
    'Authorization': API_KEY,
    'Accept': 'application/prs.coverage+json, application/json',
    'User-Agent': 'Regioweer-Rico/1.0',
})
with urlopen(req, timeout=30) as r:
    obj = json.load(r)


def coverage(o):
    if isinstance(o, dict) and o.get('type') == 'CoverageCollection':
        covs = o.get('coverages') or []
        return covs[0] if covs else o
    return o

cov = coverage(obj)
ranges = cov.get('ranges', {}) if isinstance(cov, dict) else {}
key = next((k for k in ranges if k.lower() == 'ta'), None)
if key is None:
    key = next((k for k in ranges if 'temperature' in k.lower()), None)
if not key:
    raise SystemExit(f'Geen temperatuurreeks in EDR-antwoord: {list(ranges)}')
values = ranges[key].get('values') or []

# CoverageJSON time axis: usually domain.axes.t.values.
domain = cov.get('domain', {}) if isinstance(cov, dict) else {}
axes = domain.get('axes', {}) if isinstance(domain, dict) else {}
times = (axes.get('t') or {}).get('values') or []
if len(times) != len(values):
    raise SystemExit(f'Tijd/temperatuur-lengte ongelijk: {len(times)} / {len(values)}')

by_day = {}
for ts, raw in zip(times, values):
    if raw is None:
        continue
    try:
        v = float(raw)
    except (TypeError, ValueError):
        continue
    # Defensive conversion if a future response uses Kelvin.
    if v > 150:
        v -= 273.15
    try:
        dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00')).astimezone(timezone.utc)
    except ValueError:
        continue
    day = dt.date().isoformat()  # KNMI climate day is 00-24 UTC.
    row = by_day.setdefault(day, {'values': [], 'last_observation': None, 'current': None})
    row['values'].append(v)
    if row['last_observation'] is None or dt.isoformat() > row['last_observation']:
        row['last_observation'] = dt.isoformat().replace('+00:00', 'Z')
        row['current'] = v

out_days = {}
for day, row in sorted(by_day.items()):
    vals = row['values']
    if not vals:
        continue
    out_days[day] = {
        'tx': round(max(vals), 1),
        'tn': round(min(vals), 1),
        'current': round(row['current'], 1) if row['current'] is not None else None,
        'count': len(vals),
        'last_observation': row['last_observation'],
        'basis': '10-minute air temperature (ta)',
    }

payload = {
    'status': 'ok',
    'station': 'De Bilt',
    'station_id': '0-20000-0-06260',
    'updated_at': now.isoformat().replace('+00:00', 'Z'),
    'day_definition': '00:00-24:00 UTC',
    'source': 'KNMI EDR 10-minute-in-situ-meteorological-observations',
    'days': out_days,
}
out_path = Path(os.environ.get('OUTPUT_PATH', 'data/debilt-actueel.json'))
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Wrote {out_path} with {len(out_days)} day(s)')
