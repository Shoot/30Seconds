# 30Seconds

Websocket implementation of a popular board game. This could easily be adapted into other games, as the only thing that would differ would be the `game`/`round` portion.

## Getting Started

### Requirements
- Python 3

### Installation
```
git clone https://github.com/Shoot/30Seconds.git
```

### Usage
Start by initializing a new virtual environment within your cloned repository. This can be done by typing:
```
py -m venv venv
```
Once you have initialized it, you can activate it by typing:
```
# On Unix
source venv/bin/activate

# On Windows
venv\Scripts\activate
```
Once you are in your virtual environment, type the following in order to get the required packages for the server:
```
pip install -r requirements.txt
```
From here, you can start the server by typing:
```
py main.py
```

## Responses

All responses from the server will be in JSON, and will follow this format:
```
{
	"s": 0/1, 				# Whether or not the action was successful
	"c": "RETURN_CODE",		# The error/success code
	"d": {					# Any data returned from the action
		"foo": "bar"
	}
}
```

### Success

Successful responses will be returned with a success value of `1`, with the following codes:

|Code|Description|
|-|-|
|CONNECT_START|Wait for the user to send information about themselves|
|HELLO|Give the user their name, UID, and group|
|CHAT_MESSAGE|New chat message received from the user's group|
|GROUP_JOIN|Another user has joined the group|
|GROUP_LEFT|Another user has left the group|
|USER_UPDATE|Another user has updated information about themselves|
|GAME_START|The group's game has started|
|GAME_END|The group's game has ended|
|ROUND_START|A new round has started|
|ROUND_END|The current round has ended|
|QUESTIONER_START|User is the questioner, and is given the words that the answerer must guess|
|ANSWERER_START|User is the answerer, and must guess the words the questioner has|

### Error

Errors will be returned with a success value of `0`, and have the following codes:

|Code|Description|
|-|-|
|INVALID_JSON|Data received was not in a valid JSON format|
|NO_DATA|No data was received from the `d` variable when there should be data|
|NO_GROUP|User tried to do an action which can only be done in a group, such as sending a message or starting a game|
|INVALID_MESSAGE|Chat message sent is empty and/or contained illegal characters|
|CANT_MESSAGE|User is not allowed to message the group, either because they have been muted (TBA) or because they are a questioner|
|INVALID_NAME|User tried to change their name to be empty, their current name, or something too long|
|TAKEN_NAME|Name is already taken by another group member|
|INVALID_GROUP|Tried to make a new, random group 5+ times, but failed|
|GROUP_EXISTS|Tried to create a group that already exists|
|INVALID_STRING|Given string contained illegal characters|
|MAX_MEMBERS|Group has the maximum amount of people allowed|
|CANT_START|Member count is not sufficient to start the game, it must be above 4 and a multiple of 2|
|IN_GROUP|Already in the group user wants to join|
|IN_GAME|The target group is in a game already|