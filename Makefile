.EXPORT_ALL_VARIABLES:

RASA_DUCKLING_HTTP_URL = http://localhost:8000
RASA_X_PASSWORD = Qwe123123
ACTION_ENDPOINT = http://localhost:5055/webhook

clean:
	rm -rf models/

train:
	poetry run rasa train $(args)

shell:
	poetry run rasa shell $(args)

apiserver:
	poetry run uvicorn api.main:app --host 0.0.0.0 --port 8002 --loop asyncio --reload --reload-dir api

rasaserver:
	poetry run rasa run --enable-api $(args)

actionserver:
	poetry run rasa run actions $(args)

x:
	poetry run rasa x $(args)

cleanx:
	rm -rf events.db* rasa.db*
