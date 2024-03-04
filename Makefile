lint:
	poetry run black src --line-length 100
	poetry run flake8 src --max-line-length 100 --ignore F401
