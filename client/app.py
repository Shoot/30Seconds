from quart import Quart, render_template, send_from_directory
import os

app = Quart(__name__)

@app.route('/')
async def index():
	return await render_template('index.html')

@app.route('/favicon.ico')
async def favicon():
	return send_from_directory(os.path.join(app.root_path, 'static'),
		'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
	app.run(host='localhost', port=1234, debug=True)