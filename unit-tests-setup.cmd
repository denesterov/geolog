python3 -m venv .venv

call .venv/Scripts/activate

pip install -r src/requirements.txt
pip install -r test/requirements-test.txt

call .venv/Scripts/deactivate
