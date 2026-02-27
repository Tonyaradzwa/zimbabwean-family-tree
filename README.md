# Zimbabwean Family Tree Backend

Production-ready backend for scalable Zimbabwean family trees with Shona kinship.

## Development

```bash
# Install dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## Features

- Store individuals and relationships (parent, spouse, child)
- Automatic Shona kinship inference (to be expanded)
- Clean, modular layout for easy future frontend/API growth

## License

MIT