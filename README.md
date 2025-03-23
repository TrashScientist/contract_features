# Contract Feature Engineering

A FastAPI-based service for processing contract data and calculating features.

## Features

- Process contract data from CSV files
- Calculate various contract-related features
- RESTful API endpoints for feature calculation
- Docker support for easy deployment

## Prerequisites

- Python 3.9+
- Docker (optional)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd contract-features
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Docker

Build and run using Docker:

```bash
# Build the image
docker build -t contract-features .

# Run the container
docker run -p 8000:8000 contract-features
```

## Usage

### API Server

Start the FastAPI server:

```bash
python run.py --serve
```

The API will be available at `http://localhost:8000`

### CSV Processing

Process a CSV file:

```bash
python run.py --input data.csv --output features.csv
```

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

MIT License 