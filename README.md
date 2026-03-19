# Zimbabwean Family Tree

Full-stack project for scalable Zimbabwean family trees with Shona kinship.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start server  (always use python3 -m uvicorn to avoid interpreter mismatch)
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running the test suite

A basic integration test suite exercises the individuals CRUD endpoints using
FastAPI's `TestClient`. To run the tests make sure `pytest` is installed
(which you can add via `pip install pytest`), then:

```bash
# from project root
PYTHONPATH=. pytest
```

You can target a single file or test function with the same command, e.g.

```bash
PYTHONPATH=. pytest tests/test_individuals.py
PYTHONPATH=. pytest tests/test_individuals.py::test_individuals_crud
```

The tests automatically recreate `test.db` before each run, so they start
from a clean database. When you add new endpoints later, simply extend the
`tests/test_individuals.py` file or create additional test modules.


## Features

- Store individuals and relationships (parent, spouse, child)
- Automatic Shona kinship inference (to be expanded)
- Clean, modular layout for easy future frontend/API growth

## License

MIT