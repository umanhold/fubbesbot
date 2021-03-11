import telegram
import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)
from fubbes import (match_club, matchdays, current_season, ical, current_time, time2str, tz_syntax,
df_set_difference, appcal2df)
from datetime import datetime, timedelta, time, timezone
import io
from fubbes_def import (TOKEN, cal_folder, club_folder, confirm, reject, TIME_ZONES)


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEZONE, TIMEZONE2, CLUB, CLUB2, RESTART, PAUSE, TIMEZONE3, ALTERTIMEZONE = range(8)

def start(update, context):
	
	logger.info('Bot gestartet')
	user = update.message.from_user
	time_str = time2str(current_time('Europe/Berlin'))
	text = f'Hey {user.name}! I\'m a football calendar bot.\
	First I need to know your local time zone.\
	The default is Europe/Berlin ({time_str}).\
	Do you want to keep it?'
	buttons = [['Yes'],['No']]
	update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
	return TIMEZONE


def timezone(update, context):

	reply = update.message.text
	logger.info('timezone: %s', reply)

	if reply in confirm:
		context.chat_data['tz'] = 'Europe/Berlin'
		text = 'What\'s your club?'
		update.message.reply_text(text)
		return CLUB

	elif reply in reject:
		time = current_time('Europe/Berlin')
		time_str = time2str(time)
		text = f'Type the difference in hours to the time in Europe/Berlin ({time_str}).'
		exp = f'\n\nExamples:\n\
		-1 for {time2str(time + timedelta(hours=-1))}\n\
		+3 for {time2str(time + timedelta(hours=+3))}\n\
		+3.5 for {time2str(time + timedelta(hours=+3.5))}\n\
		+4,75 for {time2str(time + timedelta(hours=+4.75))}\n'
		update.message.reply_text(text+exp)
		return TIMEZONE2

def timezone2(update, context):

	reply = update.message.text
	logger.info('timezone2: %s', reply)
	syntax, reply = tz_syntax(reply)

	if syntax == 'good':
		try:
			tz = TIME_ZONES[reply]
			context.chat_data['tz'] = tz
			buttons = [['Yes'],['No']]
			text = f'Is {time2str(current_time(tz))} your local time?'
			update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
			return TIMEZONE

		except:
			text = 'Please check your watch!'
			update.message.reply_text(text)
			return TIMEZONE2

	else:
		update.message.reply_text('Please have a look at the examples!')
		return TIMEZONE2

def club(update, context):
	
	user = update.message.from_user
	reply = update.message.text
	logger.info('Club: %s', reply)

	club, club_url = match_club(reply)

	if club_url is not None:

		context.chat_data['club'] = club
		context.chat_data['club_url'] = club_url
		tz = context.chat_data['tz']
		buttons = [['Yes'],['No']]

		if reply.lower() == club.lower():

			# create calendar
			try:
				df = matchdays(club_url,current_season(),tz)
				club_ = club.replace(' ','_')
				name = f'{user.id}_{club_}'
				data = appcal2df(df,cal_folder,name)
				ical(data,cal_folder,name)

				# list of dictonaries with calendars
				d = {
					'club_url': club_url,
					'club': club,
					'club_': club_,
					'data': data,
					'name': name		
				}

				try: 
					context.chat_data['cal'].append(d)
				except KeyError:
					context.chat_data['cal'] = [d]

				# send link to calendar file
				text = f'http://fubbesbot.ddns.net/{user.id}_{club_}.ics'
				update.message.reply_text(text)

				# ask for restart
				buttons = [['Yes'],['No']]
				text = 'Would you like to have another calendar?'
				update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
				return RESTART

			except:
				text = 'Sorry! Something went wrong.'
				update.message.reply_text(text)
				text = 'What\'s your club again?'
				update.message.reply_text(text)
				return CLUB

		else:
			text = f'Is {club} your club?'
			update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
			return CLUB2

	elif int(len(club)) in range(2, 6):
		text = 'Choose your club'
		update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup([club], one_time_keyboard=True))
		return CLUB

	else:
		text = 'Not precise enough. Please check the spelling of your club'
		update.message.reply_text(text)
		return CLUB


def club2(update, context):
	
	user = update.message.from_user
	reply = update.message.text
	logger.info('Club2: %s', reply)

	club = context.chat_data['club']

	if reply in reject:
		update.message.reply_text('What\'s your club?')
		return CLUB

	elif reply in confirm:
		
		# create calendar
		df = matchdays(club_url,current_season(),tz)
		club_ = club.replace(' ','_')
		name = f'{user.id}_{club_}'
		data = appcal2df(df,cal_folder,name)
		ical(data,cal_folder,name)


		# list of dictonaries with calendars
		d = {
			'club_url': club_url,
			'club': club,
			'club_': club_,
			'data': data,
			'name': name		
		}

		try: 
			context.chat_data['cal'].append(d)
		except KeyError:
			context.chat_data['cal'] = [d]

		# send link to calendar file
		text = f'http://fubbesbot.ddns.net/{user.id}_{club_}.ics'
		update.message.reply_text(text)

		# ask for restart
		buttons = [['Yes'],['No']]
		text = 'Would you like to have another calendar?'
		update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))

		return RESTART

	else:
		update.message.reply_text('Yes or no?')
		return CLUB2

def restart(update, context):
	
	reply = update.message.text
	logger.info('Restart?: %s', reply)

	tz = context.chat_data['tz']
	dlist = context.chat_data['cal']

	if reply == 'Add' or reply in confirm:
		text = 'Which club?'
		update.message.reply_text(text)
		return CLUB

	elif reply == 'Update':
		for d in dlist:
			df = df_set_difference(d['data'],matchdays(d['club_url'],current_season(),tz))
			if df.empty == True:
				club = d['club']
				text = f'Nothing to update for {club}!'
				update.message.reply_text(text)
			else:
				name, club = d['name'], d['club']
				data = appcal2df(df,cal_folder,name)
				ical(data,cal_folder,name)
				d['data'] = data
				text = f'{club} calendar has been updated!'
				update.message.reply_text(text)
		context.chat_data['cal'] = dlist
		return PAUSE

	elif reply == 'Timezone':
		time = current_time('Europe/Berlin')
		time_str = time2str(time)
		text = f'Type the difference in hours to the time in Europe/Berlin ({time_str}).'
		exp = f'\n\nExamples:\n\
		-1 for {time2str(time + timedelta(hours=-1))}\n\
		+3 for {time2str(time + timedelta(hours=+3))}\n\
		+3.5 for {time2str(time + timedelta(hours=+3.5))}\n\
		+4,75 for {time2str(time + timedelta(hours=+4.75))}\n'
		update.message.reply_text(text+exp)
		return TIMEZONE3

	elif reply in reject:
		text = 'Alright! Let me know when you need me again.'
		update.message.reply_text(text)
		return PAUSE

	else:
		return PAUSE

def pause(update, context):

	reply = update.message.text
	logger.info('User says: %s', reply)

	# ask for restart
	buttons = [['Update'],['Add'],['Timezone']]
	text = 'Would you like to update your calendar, add another one, or change the time zone?'
	update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))

	return RESTART


def timezone3(update, context):

	reply = update.message.text
	logger.info('timezone3: %s', reply)

	syntax, reply = tz_syntax(reply)

	if syntax == 'good':
		try:
			tz = TIME_ZONES[reply]
			context.chat_data['tz'] = tz
			buttons = [['Yes'],['No']]
			text = f'Is {time2str(current_time(tz))} your local time?'
			update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
			return ALTERTIMEZONE

		except:
			text = 'Please check your watch!'
			update.message.reply_text(text)
			return TIMEZONE3

	else:
		update.message.reply_text('Please have a look at the examples!')
		return TIMEZONE3

def altertimezone(update, context):

	user = update.message.from_user
	reply = update.message.text
	logger.info('altertimezone: %s', reply)

	dlist = context.chat_data['cal']
	tz = context.chat_data['tz']

	if reply in confirm:
		
		for d in dlist:
			data = d['data']
			data['begin'] = data['begin'].dt.tz_convert(tz=tz)
			data['end'] = data['end'].dt.tz_convert(tz=tz)
			d['data'] = data
			club_ = d['club_']
			club = d['club']
			name = f'{user.id}_{club_}'
			ical(data,cal_folder,name)
			text = f'The timezone has been altered for {club}.'
			update.message.reply_text(text)
		context.chat_data['cal'] = dlist

		return PAUSE

	elif reply in reject:

		return TIMEZONE3


def main():
	updater = Updater(TOKEN, use_context=True)
	dp = updater.dispatcher    

	conv_handler = ConversationHandler(
		entry_points=[CommandHandler('start', start)],
		states={
			CLUB: [MessageHandler(Filters.text, club)],
			CLUB2: [MessageHandler(Filters.text, club2)],
			TIMEZONE: [MessageHandler(Filters.text, timezone)],
			TIMEZONE2: [MessageHandler(Filters.text, timezone2)],
			TIMEZONE3: [MessageHandler(Filters.text, timezone3)],
			ALTERTIMEZONE: [MessageHandler(Filters.text, altertimezone)],
			RESTART: [MessageHandler(Filters.text, restart)],
			PAUSE: [MessageHandler(Filters.text, pause)],	

		},
		fallbacks=[]
	)
	dp.add_handler(conv_handler)
	updater.start_polling()
	updater.idle()

if __name__ == '__main__':
	main()