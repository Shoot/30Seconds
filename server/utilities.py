import json
import random

from .constants import *

class Word:
	def __init__(self, word):
		self.word = word
		self.scored = False

with open('server/words/countries.txt', 'r', encoding='utf-8') as file:
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