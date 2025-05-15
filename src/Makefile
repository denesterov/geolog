#!/bin/bash

venv:
	python3 -m venv venv

.PHONY: setup run cleanup test test-docker

setup: venv
	. venv/bin/activate; pip install -r requirements.txt

cleanup:
	rm -rf ./venv

run: venv
	@TELE_BOT_TOKEN_M=$(shell cat bot_token.txt); \
	export TELE_BOT_TOKEN=$$TELE_BOT_TOKEN_M; \
	. venv/bin/activate; python3 geobot.py

run_env_token: venv
	. venv/bin/activate; python3 geobot.py

test: venv
	. venv/bin/activate; pip install -r ../test/requirements-test.txt; \
	PYTHONPATH=. pytest -v -c ../test/pytest.ini

test-docker:
	cd ../test/docker && docker-compose up --build --abort-on-container-exit
