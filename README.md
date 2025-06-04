# recruiter-agent

python -m venv .venv
.venv\Scripts\Activate.ps1

pip install pip-tools
pip-compile requirements.in
pip install -r requirements.txt

$env:PYTHONPATH = "src"
python .\run.py


ruff check . --fix
isort .
black .

