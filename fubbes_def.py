from dotenv import load_dotenv
import os
load_dotenv()

TOKEN = os.environ['TOKEN']
cal_folder = os.environ['cal_folder']
club_folder = os.environ['club_folder']

confirm = ['yes','Yes','y','Ja','ja','j']
reject = ['no','No','n','Nein','nein'] 

TIME_ZONES = {
	'+11.75': 'NZ-CHAT', # utc+12 3/4
	'+11': 'Pacific/Fiji', # utc+12
	'+10': 'Asia/Magadan', # utc+11
	'+9': 'Australia/Melbourne', # utc+10
	'+8.5': 'Australia/Darwin', # utc+9 1/2
	'+8': 'Asia/Tokyo', # utc+9
	'+7.75': 'Australia/Eucla', # utc+8 3/4
	'+7': 'Asia/Brunei', # utc+8
	'+6': 'Asia/Novosibirsk', # utc+7
	'+5.5': 'Asia/Rangoon', # utc+6 1/2
	'+5': 'Asia/Dhaka', # utc+6
	'+4.75': 'Asia/Katmandu', # utc+5 3/4
	'+4.5': 'Asia/Kolkata', # utc+5 1/2
	'+4': 'Indian/Maldives', # utc+5
	'+3.5': 'Asia/Kabul', # utc+4 1/2
	'+3': 'Indian/Mauritius', # utc+4
	'+2.5': 'Iran', # utc+3 1/2
	'+2': 'Europe/Moscow', # utc+3
	'+1': 'EET', # utc+2
	'+0': 'Europe/Berlin', # utc+1
	'-0': 'Europe/Berlin', # utc+1
	'0': 'Europe/Berlin', # utc+1
	'-1': 'Europe/London', # utc-0
	'-2': 'Atlantic/Cape_Verde', # utc-1
	'-3': 'Atlantic/South_Georgia',  # utc-2
	'-4': 'Brazil/East', # utc-3
	'-5': 'Brazil/West', # utc-4
	'-6': 'America/New_York',  # utc-5
	'-7': 'America/Mexico_City', # utc-6
	'-8': 'America/Denver', # utc-7
	'-9': 'America/Los_Angeles', # utc-8
	'-10': 'US/Alaska', # utc-9
	'-11.5': 'Pacific/Marquesas', # utc-9 1/2
	'-12': 'US/Hawaii', # utc-10
	'-13': 'US/Samoa' # utc-11
}

COMP_MAP_ABBRV = {
	'Bundesliga': 'BL',
	'2. Bundesliga': 'BL2',
	'3. Liga': 'L3',
	'Champions League': 'CL',
	'Europa League': 'EL',
	'DFB-Pokal': 'DFB',
	'Europa League': 'EL',
	'Europa League Qual.': 'ELQ',
	'Freundschaft Vereine': 'FS',
	'Klub-WM': 'KWM'
}