import json
import os
import random
import string

from . import constants

def generate_wordlist():
	words = []
	for wordlist in os.listdir('server/words'):
		if not wordlist.endswith('.txt'):
			continue

		with open('server/words/' + wordlist, 'r') as file:
			for word in file.read().split('\n'):
				if word in {'', None}:
					continue

				words.append(word)

	return words

words = generate_wordlist()

def random_string(length):
	return ''.join(
		random.choice(string.ascii_letters+string.digits) for i in range(length)
	)

def validate_string(string):
	if not 0 < len(string) < 32:
		return False

	for letter in string:
		if letter not in constants.CHARSET:
			return False

	return True

def sanitize_string(string):
	return string.encode('utf-8', 'ignore').decode('utf-8').strip()

def is_json(data):
	try:
		data = json.loads(data)
		return data
	except json.JSONDecodeError:
		return False

def get_random_word():
	return random.choice(words)