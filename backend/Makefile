dev:
	FLASK_APP=ll/run.py FLASK_DEBUG=1 flask run
prod:
	gunicorn ll.run:app
test:
	pytest