import json
import random
import string
import websockets
from datetime import datetime

from . import constants
from . import group

class Word:
	def __init__(self, word):
		self.word = word
		self.scored = False

	def __str__(self):
		return self.word

with open('server/words/word_list.txt', 'r', encoding='utf-8') as file:
	words = file.read().split('\n')

def random_string(length):
	return ''.join(random.choice(string.ascii_letters+string.digits) for i in range(length))

def validate_string(string):
	if not 0 < len(string) < 32:
		return False

	for letter in string:
		if letter not in constants.VALID_CHARSET:
			return False

	return True

def sanitize_string(string):
	return string.encode('utf-8', 'ignore').decode('utf-8').strip()

def is_json(data):
	try:
		data = json.loads(data)
		return data
	except Exception as e:
		return False

def message(success, code, data=None):
	return json.dumps({
		's': success,
		'c': code,
		'd': data
	})

def get_random_word():
	return Word(random.choice(words))

def log(message, data=None):
	# Logging format:
	# [dd/mm/yyyy hh:mm] [group-id]: <message>
	if data is None:
		extra_data = 'server'
	elif isinstance(data, websockets.server.WebSocketServerProtocol):
		extra_data = str(data.remote_address[0]) + ':' + str(data.remote_address[1])
	elif isinstance(data, group.Group):
		extra_data = data.gid
	else:
		extra_data = type(data)

	print(f"[{datetime.now().strftime('%d/%m/%y %H:%M:%S')}] [{extra_data}]: {message}")