var colorHash = new ColorHash();

var user = {};

let searchParams = new URLSearchParams(window.location.search);

var error_codes = {
	'IN_GROUP': 'You are already in that group',
	'INVALID_JSON': 'Given data was invalid',
	'INVALID_NAME': 'That name is invalid',
	'TAKEN_NAME': 'That name is taken already',
	'CANT_START': 'There aren\'t enough players to start',
	'RATE_LIMIT': 'You are sending messages too quickly'
}

function show_snackbar ( text ) {
	var snackbar = $( '#snackbar' );

	snackbar.text( text );
	snackbar.addClass( 'show' );

	setTimeout( function( ) {
		snackbar.removeClass( 'show' )
	}, 3000);
}

function initialize_websocket ( address, port ) {
	let ws = new WebSocket('ws://' + address + ':' + port);

	$('#group-members').on('click', '.name-form', function(e) {
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

	$('#group-landing').on('click', '.start-game', function() {
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

	ws.onopen = function(e) {
		$('#landing').hide();
		$('#connection').show();

		$('.connection-status').text('Connected!');

		console.log('[open] Started the connection');
	}

	ws.onmessage = function(event) {
		var data = JSON.parse(event.data);
		if (data.s) {
			switch (data.c) {
				case 'CONNECT_START':
					ws.send(JSON.stringify({
						'c': 'NEW_CONNECT',
						'd': {
							name: $('#nickname').val()
						}
					}));

					$('#group-container').show();

					break;
				case 'HELLO':
					user = data.d;

					var group = null;
					if (searchParams.has('group')) {
						group = searchParams.get('group');
					}

					ws.send(JSON.stringify({
						c: 'JOIN_GROUP',
						d: {
							group: group
						}
					}));
					break;
				case 'GROUP_JOIN':
					$('.copy-invite').attr('data-clipboard-text', 'http://localhost:1234/?group=' + data.d.name);

					$('#connection').hide();
					$('#group-landing').show();

					$('.group-header').text(data.d.name);

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
					$('#game-container').show();

					$.each(data.d.teams, function(index, team) {
						$('#team-list').append('<tr><th>team ' + (index + 1) + '</th><td>' + team[0].name + '</td><td>' + team[1].name + '</td></tr>');
					});

					break;
				case 'ROUND_START':
					$('.game-role').text('you are a spectator');
					$('#word-list').empty();

					for (var i = 0; i < 5; i++) {
						$('#word-list').append('<tr><td class="incorrect">???</td></tr>');
					}

					break;
				case 'ROUND_END':
					$('#word-list').empty();

					$.each(data.d.words, function(index, word) {
						$('#word-list').append('<tr><td class="' + (word[1] ? 'correct' : 'incorrect') + '">' + word[0] + '</td></tr>');
					});

					break;
				case 'CHAT_MESSAGE':
					$('#incoming-messages').append('<tr><td>' + data.d.user.name + ': ' + data.d.message + '</td></tr>');

					break;
				case 'QUESTIONER_START':
					$('.game-role').text('you are a questioner');
					$('#word-list').empty();

					$.each(data.d.words, function(index, word) {
						$('#word-list').append('<tr><td class="incorrect">' + word + '</td></tr>');
					});

					break;
				case 'ANSWERER_START':
					$('.game-role').text('you are an answerer');

					break;
				case 'CORRECT_WORD':
					var word = $('#word-list').find('td').eq(data.d.index);
					word.attr('class', 'correct');
					word.text(data.d.word);

					break;
				default:
					break;
			}
		} else {
			show_snackbar(error_codes[data.c]);
		}
	}

	ws.onclose = function(event) {
		var connection = $('#connection');
		if (event.wasClean) {
			$('.connection-status').text('Connection closed.');
			console.log('[close] Closed the connection cleanly');
		} else {
			$('.connection-status').text('Connection died!');
			console.error('[close] Connection died');
		}
		connection.show();
	}

	ws.onerror = function(error) {
		console.error('[error] ' + error.message);
	}
}

$(document).ready(function() {
	/*
	$('form input[id^=tab-]').click(function() {
		var form = $(this.form);

		var visible_index = 0;
		var previous_item = 0;
		form.find('div').each(function(index, div) {
			if ($(this).css('display') != 'none') {
				previous_item = $(this);
				visible_index = index;
			}
		});

		if ($(this).attr('id') == 'tab-next') {
			if (visible_index != (form.find('div').length - 1)) {
				previous_item.hide();
				form.find('div').eq(visible_index + 1).show();
			}
			if ((visible_index + 1) == (form.find('div').length - 1)) {
				$('#tab-submit').show();
			}
		} else {
			$('#tab-submit').hide();
			if (visible_index != 0) {
				previous_item.hide();
				form.find('div').eq(visible_index - 1).show();
			}
		}
	});
	*/
	new ClipboardJS('.copy-invite');

	if (searchParams.has('group')) {
		initialize_websocket( 'localhost', '5000' );
	}

	$('#tab-submit').click(function() {
		initialize_websocket( 'localhost', '5000' );
	});
});

function construct_user_line(index, member) {
	return '<li class="user-line"><span style="color:' + colorHash.hex(member.uid) + '">'
	+ (index + 1) + '. ' + member.name + ((member.uid == user.uid) ? '</span> <span>[<a href="#" class="name-form">change name</a>]</span>' : '')
	+ '</li>\n';
}