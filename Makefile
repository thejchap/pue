all: install example
example:
	@python -m uvicorn example:APP --reload
install:
	@python -m pip install -r requirements.txt
format:
	@python -m ruff check . --fix
deploy:
	@fly deploy
tail:
	@fly logs
