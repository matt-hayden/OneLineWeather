import datetime
import json

import os, os.path

with open('config.json') as fi:
	config = json.load(fi)

def alerts(url='http://api.wunderground.com/api/{key}/alerts/q/{location_path}.json'.format(**config) ):
	return get_json_cache(url, stale=0)
def almanac(url='http://api.wunderground.com/api/{key}/almanac/q/{location_path}.json'.format(**config) ):
	return get_json_cache(url, '.almanac.cache', stale=12*60)
def astronomy(url='http://api.wunderground.com/api/{key}/astronomy/q/{location_path}.json'.format(**config) ):
	def _totime(d):
		h = int(d.pop('hour', 0))
		m = int(d.pop('minute', 0))
		return datetime.time(hour=h, minute=m)
	a = get_json_cache(url, '.astronomy.cache', stale=12*60)
	d = a.pop('sun_phase')
	a['sunrise'] = _totime(d['sunrise'])
	a['sunset'] = _totime(d['sunset'])
	d = a.pop('moon_phase')
	d.pop('sunrise')
	d.pop('sunset')
	d.pop('current_time')
	a['moon_phase'] = d
	return a
def conditions(url='http://api.wunderground.com/api/{key}/conditions/q/{location_path}.json'.format(**config) ):
	return get_json_cache(url, '.conditions.cache', stale=15)
def forecast10day(url='http://api.wunderground.com/api/{key}/forecast10day/q/{location_path}.json'.format(**config) ):
	return get_json_cache(url, '.forecast10day.cache', stale=4*60)
def planner(start=datetime.datetime.now(), end=None, url='http://api.wunderground.com/api/{key}/planner_{start:%m%d}{end:%m%d}/q/{location_path}.json'):
	if not end:
		end = start+datetime.timedelta(days=30)
	p = dict(config)
	p['start'] = start
	p['end'] = end
	return get_json_cache(url.format(**p), 'planner.cache', stale=12*60)

# Not supported from wunderground:
def extended_forecast(*args, **kwargs):
	response = forecast10day(*args, **kwargs)
	desc = response['forecast']['txt_forecast']['forecastday']
	fore = response['forecast']['simpleforecast']['forecastday']
	twice_daily = list(zip(desc, fore))
	return list(zip(twice_daily[::2], twice_daily[1::2]))
def quick_forecast_text(*args, **kwargs):
	for (fday, fnight) in extended_forecast(*args, **kwargs):
		#day, night = daypair
		yield '☼ '+fday[0]['fcttext_metric']+' ☽ '+fnight[0]['fcttext_metric']
def will_frost(*args, **kwargs):
	a = almanac()['almanac']
	normal = float(a['temp_low']['normal']['C'])
	record = float(a['temp_low']['record']['C'])
	#f = forecast10day(*args, **kwargs)
	if normal <= 0:
		return 1
	if record <= 0:
		return 1/(normal-record)
	else:
		return 0

# helper functions
def get_json_cache(url, cache_file='.cache', stale=75, parsed_json=None):
	import pickle
	if os.path.exists(cache_file):
		import time
		mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.stat(cache_file)
		if size and (time.time() < mtime + stale*60):
			with open(cache_file, 'rb') as fi:
				parsed_json = pickle.load(fi)
	if not parsed_json:
		import requests
		r = requests.get(url)
		assert 200 <= r.status_code < 300
		parsed_json = json.loads(r.text)
		if parsed_json:
			try:
				with open(cache_file, 'wb') as fo:
					pickle.dump(parsed_json, fo)
			except:
				pass
	return parsed_json

#
if __name__ == '__main__':
	for line in quick_forecast_text():
		print(line)
