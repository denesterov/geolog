#!/bin/bash

.PHONY: setup run cleanup test test-docker test-unit

.venv:
	python3 -m venv .venv

setup: .venv	
	.venv/bin/activate; pip install -r src/requirements.txt

cleanup:
	rm -rf ./venv

run: .venv
	@TELE_BOT_TOKEN_M=$(shell cat src/bot_token.txt); \
	export TELE_BOT_TOKEN=$$TELE_BOT_TOKEN_M; \
	.venv/bin/activate; cd src && python3 geobot.py

run_env_token: .venv
	.venv/bin/activate; cd src && python3 geobot.py

test: .venv
	.venv/bin/activate; pip install -r test/requirements-test.txt; \
	$env:PYTHONPATH="src"; pytest -v -c test/pytest.ini

test-unit: .venv
	.venv/bin/activate; pip install -r test/requirements-test.txt; \
	$env:PYTHONPATH="src"; pytest -v test/unit/test_session_data.py -c test/pytest.ini

test-docker:
	cd test/docker && docker compose up --build --abort-on-container-exit --exit-code-from test
