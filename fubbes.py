import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import bs4
import os
import re
from datetime import datetime, timedelta, time
import pytz
from pytz import timezone
from icalendar import Calendar, Event
from fubbes_def import COMP_MAP_ABBRV, club_folder

# methods

def convert_tz(data, tz):
	columns = ['begin','end']
	for c in columns:
		data[c] = pd.to_datetime(data[c], utc=True)
		data[c] = data[c].dt.tz_convert(tz=tz)
	return data

def dtstr2dtaw(string, tz):
	""" takes date string of format %d.%m.%Y (%H:%M)
	and returns aware datetime """
	
	r1 = re.compile('\d{2}.\d{2}.\d{4} \d{2}:\d{2}')
	r2 = re.compile('\d{2}.\d{2}.\d{4}')
	
	assert (r1.match(string), r2.match(string)) != (None, None)
	
	if r1.match(string) is not None:
		fmt = '%d.%m.%Y %H:%M'
	elif r2.match(string) is not None:
		fmt = '%d.%m.%Y'
	return pytz.timezone(tz).localize(datetime.strptime(string, fmt), is_dst=None)

def mvelm2nxarr(arrlist, value):
	""" takes list of arrays and moves elements at a position
	larger than value to the first position of the next array 
	and limits the arrays to the length of value """
	i = 1
	l = []
	for arr in arrlist:
		if i == 1:
			if len(arr) > value:
				x, y, z = arr[:value], arr[value:], arr
				l.append(x)
			else:
				l.append(arr)
		elif i > 1:
			try:
				if len(z) > value:
					arr = np.concatenate((y,arr))
				if len(arr) > value:
					x, y, z = arr[:value], arr[value:], arr
					l.append(x)
				else:
					l.append(arr)
			except:
				l.append(arr)
		i += 1
	return l

def df_set_difference(df1,df2):
	""" returns data that is in df2 but not in df1 """
	df1['date'] = df1.apply(lambda x: x['begin'].date(), axis=1)
	df2['date'] = df2.apply(lambda x: x['begin'].date(), axis=1)
	df = pd.concat([df1, df2]).drop_duplicates(subset=['date','name'], keep=False)
	return df.drop(['date'], axis=1)

def current_time(tz):
	""" returns current time for specified time zone """
	return pytz.utc.localize(datetime.utcnow(), is_dst=None).astimezone(timezone(tz))

def time2str(time):
	""" returns utc time as hh:mm string """
	minute = '0'+str(time.minute) if time.minute < 10 else str(time.minute)
	return str(time.hour)+':'+minute

def tz_syntax(string):
	""" returns 'good' and clean reply if reply to adjust the current time zone is fine """
	signs = ['+','-']
	cond = all(len(s) <= 2 for s in string[1:].replace(',','.').split('.'))
	if string[0] in signs and cond == True or string == '0':
		return 'good', string.replace(',','.').strip()
	else:
		return None, None

def current_season():
	""" returns the latter year of current season """
	year, month = datetime.today().year, datetime.today().month
	return year-1 if month <= 6 else year

def match_club(string):
	""" takes user reply and matches club name from csv """
	os.chdir(club_folder)
	df = pd.read_csv('clubs.csv', index_col=0)
	string = string.lower()
	df_match = df[df.Club_Lower.eq(string)]
	if df_match.empty:
		df['Match'] = df['Club_Lower'].str.contains(string, regex=True)
		club = df.loc[(df['Match'] == True)]['Club'].tolist()
		club_url = None
	else:
		club = df_match['Club'][0]
		club_url = df_match['Club_Url'][0]
	return club, club_url

def weltfussball(club_url, season):
	""" return soup for club and seaons """
	season += 1
	url = f'https://www.weltfussball.de/teams/{club_url}/{season}/3/'
	r = requests.get(url)
	if r:
		return BeautifulSoup(r.text, 'html5lib')
	else:
		return None

def comp_clean(string):
	""" returns competition w/o season """
	p1 = r'\d{4}\/\d{4}'
	p2 = r'\d{4}'
	if re.search(p1, string) is not None:
		string = string.replace(re.search(p1, string)[0],'').strip()
	elif re.search(p2, string) is not None:
		string = string.replace(re.search(p2, string)[0],'').strip()
	return string

def comp_chunks(td, td_title):
	""" returns list of tuples to slice td list w.r.t competition """
	tups = []
	i, x, y = 0, 0, 0
	for t in td:
		try:
			if t == td_title[i]:
				if i > 0:
					tups.append((x,y-1))
				i += 1
				x = y
		except IndexError:
			pass
		y += 1
	tups.append((x,len(td)))
	return tups

def cm2df(comp_mday, tz):
	""" returns dataframe of dictionary with competiions and match days """
	data = []
	for comp in comp_mday:
		for m in comp_mday[comp]:
			
			date = m[2].get_text()
			hour = m[3].get_text()
			loc = m[4].get_text()
			opp = m[6].contents[1].get_text()

			if len(m[7].contents) > 1:
				res = m[7].contents[1].get_text().strip()
			else:
				res = m[7].contents[0].strip()
					
			if hour == '':
				begin, end = dtstr2dtaw(f'{date}', tz), dtstr2dtaw(f'{date}', tz)
			else:
				begin = dtstr2dtaw(f'{date} {hour}', tz)
				end = begin + timedelta(minutes=110)

			competition = comp_clean(comp)
			if competition in COMP_MAP_ABBRV:
				competition = COMP_MAP_ABBRV[competition]

			if res != '-:-':
				name = f'{competition} {loc} {opp} {res}'
			else:
				name = f'{competition} {loc} {opp}'

			d = {
				'begin': begin,
				'end': end,
				'name': name
			}
			data.append(d)

	return pd.DataFrame(data=data)

def matchdays(club_url, season, tz):
	""" returns match days data """
	soup = weltfussball(club_url, season)
	tbody = soup.find_all('tbody')
	td = tbody[1].find_all('td')
	colspan = td[0]['colspan']
	td_title = tbody[1].find_all('td', attrs={'class': 'hell', 'colspan': colspan})
	comp = [td[c[0]:c[1]] for c in comp_chunks(td, td_title)]
	comp_mday = {}
	for c in comp:
		lstarr = np.split(np.array(c, dtype=object), len(c)/int(colspan))
		comp_mday[c[0].get_text()] = mvelm2nxarr(lstarr, int(colspan))
	return cm2df(comp_mday, tz)


def ical(data,path,name):
	""" creates ical file of data at path """

	os.chdir(path)
	cal = Calendar()
	for index, row in data.iterrows():

		event = Event()
		event.add('dtstart', row['begin'])
		event.add('dtend', row['end'])
		event.add('summary', row['name'])
		cal.add_component(event)

	f = open(name+'.ics', 'wb')
	f.write(cal.to_ical())
	f.close()