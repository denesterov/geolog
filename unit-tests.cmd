python3 -m venv .venv

call .venv/Scripts/activate

pip install -r src/requirements.txt
pip install -r test/requirements-test.txt

set PYTHONPATH=src;test
pytest -v test/unit/ -c test/pytest.ini

call .venv/Scripts/deactivate
