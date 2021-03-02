import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
import os
from fubbes_def import club_folder

COMP_MAP_BASE = {
	'1. Bundesliga': 'bundesliga',
	'BL': 'bundesliga',
	'1. BL': 'bundesliga',
	'2. Bundesliga': '2-bundesliga',
	'2. BL': '2-bundesliga',
	'3. BL': '3-liga',
	'PL': 'eng-premier-league',
	'CS': 'eng-championship',
	'EL1': 'eng-league-one',
	'EL2': 'eng-league-two',	
	'NAT': 'eng-national-league',
	'SA': 'ita-serie-a',
	'SB': 'ita-serie-b',
	'SC': 'ita-serie-c',
	'PD': 'esp-primera-division',
	'SD': 'esp-segunda-division',
	'FL1': 'fra-ligue-1',
	'FL2': 'fra-ligue-2',
	'ERD': 'ned-eredivisie',
	'EED': 'ned-eerste-divisie'
}

COMP_MAP_DF = {
	'1. Bundesliga': '1. Bundesliga',
	'2. Bundesliga': '2. Bundesliga',
	'Premier League': 'Premier League',
	'BL': '1. Bundesliga',
	'1. BL': '1. Bundesliga',
	'2. BL': '2. Bundesliga',
	'3. BL': '3. Liga',
	'PL': 'Premier League',
	'EL1': 'League 1',
	'EL2': 'League 2',
	'CS': 'Championship',
	'NAT': 'National League',
	'SA': 'Serie A',
	'SB': 'Serie B',
	'SC': 'Serie C',
	'PD': 'Primera Division',
	'SD': 'Segunda Division',
	'FL1': 'Ligue 1',
	'FL2': 'Ligue 2',
	'ERD': 'Eredivisie',
	'EED': 'Eerste Divisie'
}


def clubs(comp, fseason, lseason):

	try:
		csv = pd.read_csv(path+'/clubs.csv')
	except:
		csv = None

	if type(comp) is not list:
		comp = [comp]

	data = []

	for c in comp:

		for season in range(fseason,lseason):

			season = str(season)+'-'+str(season+1)

			print(c, season)

			base = 'https://www.weltfussball.de/spieler/%s-%s/'
			call = base % (COMP_MAP_BASE[c], season)

			r = requests.get(call)

			if r:
				soup = BeautifulSoup(r.text, 'html5lib')
				tbody = soup.find_all('tbody')
				teams = tbody[1].find_all('td', attrs={'align': 'center', 'width': '7%'})
				country = tbody[1].find('td', attrs={'align': 'center', 'width': ''}).contents[1]['title']

				for t in teams:
					club_url = t.find('a')['href'].replace('/teams/','').replace('/','')
					club = t.find('a').contents[0]['title'].encode('iso-8859-1').decode()

					d = {
						'Country': country,
						'Competition': COMP_MAP_DF[c],
						'Club': club,
						'Club_Lower': club.lower(),
						'Club_Url': club_url,
						'Season': season,
					}
					data.append(d)

			else:
				print('Error in request of '+call)

		df = pd.DataFrame(data=data)
		df = df.drop(columns=['Season','Competition'])
		if csv is not None:
			df = csv.append(df, ignore_index=True)
		df = df.drop_duplicates(subset='Club_Url',keep='last',ignore_index=True)


		os.chdir(club_folder)
		df.to_csv('clubs.csv', index=False)


comp = [
	'1. BL','2. BL','3. BL',
	'PL','CS','EL1','EL2','NAT',
	'SA', 'SB', 'SC',
	'PD','SD',
	'FL1', 'FL2',
	'ERD', 'EED'
]

fseason = 1990
lseason = 2021

clubs(comp,fseason,lseason)


