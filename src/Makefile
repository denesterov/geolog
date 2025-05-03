#!/bin/bash

venv:
	python3 -m venv venv

.PHONY: setup, run, cleanup

setup: venv
	. venv/bin/activate; pip install -r requirements.txt

cleanup:
	rm -rf ./venv

run: venv
	@TELE_BOT_TOKEN_M=$(shell cat bot_token.txt); \
	export TELE_BOT_TOKEN=$$TELE_BOT_TOKEN_M; \
	. venv/bin/activate; python3 geobot.py
