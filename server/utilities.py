import json
import random

from .constants import *

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
		if letter not in VALID_CHARSET:
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