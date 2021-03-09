import telegram
import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)
from fubbes import (match_club, matchdays, current_season, ical, current_time, time2str, tz_syntax, df_set_difference)
from datetime import datetime, timedelta, time, timezone
import io
from fubbes_def import (TOKEN, cal_folder, club_folder, confirm, reject, TIME_ZONES)


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
logger = logging.getLogger(__name__)

CLUB, CLUB2, TIMEZONE, TIMEZONE2, RESTART, PAUSE = range(6)

def start(update, context):
	
	logger.info('Bot gestartet')
	user = update.message.from_user
	update.message.reply_text(f'Hey {user.name}!')

	text = 'What\'s your club?'
	update.message.reply_text(text)

	return CLUB

def club(update, context):
	
	user = update.message.from_user
	reply = update.message.text
	logger.info('Club: %s', reply)

	try:
		club, club_url = match_club(reply)

		if club_url is not None:

			context.chat_data['club'] = club
			context.chat_data['club_url'] = club_url
			buttons = [['Yes'],['No']]

			if reply.lower() == club.lower():
				buttons = [['Yes'],['No']]
				time = time2str(current_time(TIME_ZONES['0']))
				text = f'Europe/Berlin is the default time zone. Do you want to keep it?'
				update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
				return TIMEZONE
			else:
				text = f'Is {club} your club?'
				update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
				return CLUB2

		elif int(len(club)) in range(2, 6):
			text = 'Choose your club'
			update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup([club], one_time_keyboard=True))
			return CLUB

		else:
			text = 'Check the spelling of your club'
			update.message.reply_text(text)
			return CLUB

	except:
		text = 'Check the spelling of your club'
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
		club, club_url = match_club(club)
		context.chat_data['club'] = club
		context.chat_data['club_url'] = club_url

		buttons = [['Yes'],['No']]
		time = time2str(current_time(TIME_ZONES['0']))
		text = f'Europe/Berlin is the default time zone. Do you want to keep it?'
		update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
		return TIMEZONE

	else:
		update.message.reply_text('Yes or no?')
		return CLUB2


def timezone(update, context):

	user = update.message.from_user
	reply = update.message.text
	logger.info('timezone: %s', reply)

	try:
		tz = context.chat_data['tz']
	except:
		tz = 'Europe/Berlin'

	if reply in confirm:

		club_url = context.chat_data['club_url']
		club = context.chat_data['club']
		club_ = club.replace(' ','_')
		data = matchdays(club_url,current_season())
		name = f'{user.id}_{club_}'
		ical(data,cal_folder,tz,name)

		d = {
			'club_url': club_url,
			'club': club,
			'club_': club_,
			'data': data,
			'tz': tz,
			'name': name		
		}

		try: 
			context.chat_data['cal'].append(d)
		except KeyError:
			context.chat_data['cal'] = [d]

		url = f'http://fubbesbot.ddns.net/{user.id}_{club_}.ics'
		update.message.reply_text(url)

		# ask for restart
		buttons = [['Yes'],['No']]
		text = 'Would you like to have another calendar?'
		update.message.reply_text(text, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
		return RESTART

	elif reply in reject:
		text = 'Type the difference in hours to your local time.'
		time = current_time(TIME_ZONES['0'])
		text = f'\n\nExamples:\n\
				-1 for {time2str(time + timedelta(hours=-1))} (London)\n\
				+3 for {time2str(time + timedelta(hours=+3))} (Mauritius)\n\
				+3.5 for {time2str(time + timedelta(hours=+3.5))} (Kabul)\n\
				+4,75 for {time2str(time + timedelta(hours=+4.75))} (Katmandu)\n'
		update.message.reply_text(text)
		return TIMEZONE2

def timezone2(update, context):

	user = update.message.from_user
	reply = update.message.text
	logger.info('timezone2: %s', reply)

	if tz_syntax(reply) == 'good':
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


def restart(update, context):
	
	user = update.message.from_user
	reply = update.message.text
	logger.info('Restart?: %s', reply)

	if reply == 'Add' or reply in confirm:
		text = 'Which club?'
		update.message.reply_text(text)
		return CLUB

	elif reply == 'Update':
		dlist = context.chat_data['cal']
		for d in dlist:
			data = df_set_difference(d['data'],matchdays(d['club_url'],current_season()))
			if data.empty == True:
				club = d['club']
				text = f'Nothing to update for {club}!'
				update.message.reply_text(text)
			else:
				tz, name, club_ = d['tz'], d['name'], d['club_']
				ical(data,cal_folder,tz,name)
				text = f'{club} calendar has been updated!'
				update.message.reply_text(text)
		return PAUSE

	elif reply in reject:
		text = 'Alright! Let me know when you need me again.'
		update.message.reply_text(text)
		return PAUSE

	else:
		return PAUSE

def pause(update, context):

	user = update.message.from_user
	reply = update.message.text
	logger.info('User says: %s', reply)

	# ask for restart
	buttons = [['Update'],['Add']]
	text = 'Would you like to update your calendar or to add another one?'
	update.message.reply_text(text,reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))

	return RESTART



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