# Contract Feature Engineering

A FastAPI service for processing contract data and calculating features, with both API and command-line interfaces.

## Features

- Process contract data from JSON contracts
- Calculate contract-related features including:
  - Number of claims in last 180 days
  - Sum of disbursed bank loans
  - Days since last loan
- RESTful API endpoints for feature calculation
- Command-line interface for batch processing
- Docker support for deployment
- CI/CD pipeline with GitHub Actions
- Environment-based configuration
- Health check endpoints
- API documentation with OpenAPI/Swagger

## Prerequisites

- Python 3.9+
- Docker (optional)

## Installation

### Local Development

1. Clone the repository:
```bash
git clone <your-repo-url>
cd json_featurization
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

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Docker

Build and run using Docker:

```bash
# Build the image
docker build -t contract-features .

# Run the container
docker run -p 8000:8000 --env-file .env contract-features
```

## Usage

### Command Line Interface

Process a CSV file directly:

```bash
# Process data.csv and output to contract_features.csv
python run.py --input data/data.csv --output data/contract_features.csv

# Start the FastAPI server
python run.py --serve
```

### API Server

Once the server is running, you can access:

1. **API Documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

2. **API Endpoints**:
   - `POST /calculate-features`: Calculate features for a single application
   - `POST /batch-calculate-features`: Calculate features for multiple applications
   - `GET /health`: Health check endpoint
   - `GET /`: API information

## Configuration

The application can be configured using environment variables:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `WORKERS`: Number of worker processes (default: 4)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (development/staging/production)
- `API_VERSION`: API version (default: 1.0.0)

## Project Structure

```
json_featurization/
├── app/                    # Application source code
│   ├── main.py           # FastAPI application
│   ├── models.py         # Data models
│   ├── services.py       # Feature calculation logic
│   ├── utils.py          # Utility functions
│   └── logging_config.py # Logging configuration
├── data/                  # Data files
├── scripts/              # Utility scripts
│   └── process_csv.py    # CSV processing script
├── tests/                # Test files
│   ├── test_api.py       # API endpoint tests
│   └── test_features.py  # Feature calculation tests
├── logs/                 # Application logs
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── run.py               # CLI entry point
└── README.md            # Project documentation
```

## Development

### Running Tests

```bash
pytest
```

With coverage reporting:

```bash
pytest --cov=app
```

## CI/CD

The project includes a GitHub Actions workflow that:
1. Runs tests with coverage reporting
2. Builds and tests the Docker image

## License

MIT License

## Support

For support, please open an issue in the GitHub repository. 