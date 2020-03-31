let ws = new WebSocket('ws://localhost:5000')
var colorHash = new ColorHash();

var user = {};

var error_codes = {
	'IN_GROUP': 'You are already in that group',
	'INVALID_JSON': 'Given data was invalid',
	'INVALID_NAME': 'That name is invalid',
	'TAKEN_NAME': 'That name is taken already',
	'CANT_START': 'There aren\'t enough players to start'
}

function show_snackbar ( text ) {
	var snackbar = $( '#snackbar' );

	snackbar.text( text );
	snackbar.addClass( 'show' );

	setTimeout( function( ) {
		snackbar.removeClass( 'show' )
	}, 3000);
}

ws.onopen = function(e) {
	var loader = $('#loader');
	loader.text('Loaded!');
	loader.fadeTo('slow', 0, null);
	loader.hide();
	console.log('[open] Started the connection');
}

ws.onmessage = function(event) {
	console.log('[msg] Received data from the server');
	var data = JSON.parse(event.data);
	if (data.s) {
		switch (data.c) {
			case 'CONNECT_START':
				session_id = readCookie('session');
				if (session_id != null) {
					ws.send(JSON.stringify({
						'c': 'JOIN_GROUP',
						'd': {
							'session': session_id,
							'group': null
						}
					}));
				} else {
					ws.send(JSON.stringify({
						'c': 'NEW_CONNECT',
						'd': {
						}
					}));
				}

				$('#group-container').show();

				break;
			case 'HELLO':
				user = data.d;
				break;
			case 'GROUP_JOIN':
				$('#group-container').hide();
				$('#group-info').show();

				$('#group-name').text('Group ' + data.d.name);

				var list = $('#group-members');
				var members = data.d.members;

				list.empty();

				$.each(members, function(index) {
					list.append(construct_user_line(index, members[index]));
				})

				if ((members.length >= 4) && members.length % 2 == 0) {
					$('.start-game').prop('disabled', false)
				} else {
					$('.start-game').prop('disabled', true)
				}

				break;
			case 'GROUP_LEAVE':
				var list = $('#group-members');
				var members = data.d.members;

				list.empty();

				$.each(members, function(index) {
					list.append(construct_user_line(index, members[index]));
				})

				if ((members.length >= 4) && members.length % 2 == 0) {
					$('.start-game').prop('disabled', false);
				} else {
					$('.start-game').prop('disabled', true);
				}

				break;
			case 'USER_UPDATE':
				var list = $('#group-members');
				var members = data.d.members;

				list.empty();

				$.each(members, function(index, member) {
					list.append(construct_user_line(index, member));
				})

				break;
			case 'GAME_START':
				//$('#group-info').hide();
				$('#game-container').show();

				$.each(data.d.teams, function(index, team) {
					$('.team-list').append('<tr><th>team ' + (index + 1) + '</th><td>' + team[0].name + '</td><td>' + team[1].name + '</td></tr>');
				});

				break;
			case 'ROUND_START':
				$('.word-list').empty();

				for (var i = 0; i < 5; i++) {
					$('.word-list').append('<tr><td class="incorrect">???</td></tr>');
				}

				break;
			case 'ROUND_END':
				$('.word-list').empty();

				$.each(data.d.words, function(index, word) {
					$('.word-list').append('<tr><td class="' + (word[1] ? 'correct' : 'incorrect') + '">' + word[0] + '</td></tr>');
				});

				break;
			case 'CHAT_MESSAGE':
				$('#incoming-messages').append('<tr><td>' + data.d.user.name + ': ' + data.d.message + '</td></tr>');

				break;
			case 'QUESTIONER_START':
				$('.word-list').empty();

				$.each(data.d.words, function(index, word) {
					$('.word-list').append('<tr><td class="incorrect">' + word + '</td></tr>');
				});

				break;
			case 'CORRECT_WORD':
				var word = $('.word-list').find('td').eq(data.d.index);
				word.attr('class', 'correct');
				word.text(data.d.word);

				break;
		}
	} else {
		show_snackbar(error_codes[data.c]);
	}
}

ws.onclose = function(event) {
	var loader = $('#loader');
	if (event.wasClean) {
		loader.text('Connection closed!');
		console.log('[close] Closed the connection cleanly');
	} else {
		loader.text('Connection died!');
		console.error('[close] Connection died');
	}
	loader.show();
}

ws.onerror = function(error) {
	console.error('[error] ' + error.message);
}

$(document).ready(function() {
	$("#chat-messages").scrollTop($("#chat-messages")[0].scrollHeight);

	$('#group-info').on('click', '.name-form', function(e) {
		e.preventDefault();

		var new_name = prompt('Enter a new name', '');
		ws.send(JSON.stringify({
			c: 'EDIT_USER',
			d: {
				name: new_name
			}
		}));
	});

	$('#join-group').click(function() {
		ws.send(JSON.stringify({
			c: 'JOIN_GROUP',
			d: {
				group: $('#group-id').val()
			}
		}));
	});

	$('#leave-group').click(function() {
		ws.send(JSON.stringify({
			c: 'LEAVE_GROUP',
			d: {
				group: $('#group-id').val()
			}
		}));

		$('#group-info').hide();
		$('#group-container').show();
	});

	$('#group-info').on('click', '.start-game', function() {
		ws.send(JSON.stringify({
			c: 'GAME_START'
		}))
	});

	$('#chat').submit(function() {
		ws.send(JSON.stringify({
			c: 'CHAT_MESSAGE',
			d: {
				message: $('#chat-message').val()
			}
		}));
		$('#chat-message').val('');
	});
});

function readCookie(name) {
	var nameEQ = name + "=";
	var ca = document.cookie.split(';');
	for (var i=0;i < ca.length;i++) {
		var c = ca[i];
		while (c.charAt(0)==' ') c = c.substring(1,c.length);
		if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
	}
	return null;
}

function construct_user_line(index, member) {
	return '<li class="user-line" style="background-color:' + colorHash.hex(member.uid) + '">'
	+ (index + 1) + '. ' + member.name + ((member.uid == user.uid) ? ' <span>[<a href="#" class="name-form">change name</a>]</span>' : '')
	+ '</li>\n';
}