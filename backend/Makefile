dev:
	FLASK_APP=ll/run.py FLASK_DEBUG=1 flask run --host 0.0.0.0
prod:
	gunicorn ll.run:app
test:
	pytest
