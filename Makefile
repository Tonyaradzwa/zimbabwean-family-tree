.PHONY: install run test

install:
	pip install -r requirements.txt

run:
	python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	python3 -m pytest
