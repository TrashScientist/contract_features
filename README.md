# Contract Feature Engineering

A production-ready FastAPI service for processing contract data and calculating features.

## Features

- Process contract data from CSV files
- Calculate various contract-related features
- RESTful API endpoints for feature calculation
- Docker support for easy deployment
- Comprehensive test coverage with Codecov reporting
- CI/CD pipeline with GitHub Actions
- Production-grade logging and monitoring
- Environment-based configuration
- Health check endpoints
- API documentation with OpenAPI/Swagger

## Prerequisites

- Python 3.9+
- Docker (optional)
- Make (optional, for using Makefile commands)

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

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=term-missing

# Run tests with coverage and generate XML report
pytest --cov=app --cov-report=xml --cov-report=term-missing
```

### Code Quality

```bash
# Format code
black .
isort .

# Run linters
flake8
mypy app/
```

### API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Features

- `POST /calculate-features`: Calculate features for a single application
- `POST /batch-calculate-features`: Calculate features for multiple applications

### System

- `GET /health`: Health check endpoint
- `GET /`: API information and documentation

## Configuration

The application can be configured using environment variables:

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `WORKERS`: Number of worker processes (default: 4)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (development/staging/production)
- `API_VERSION`: API version (default: 1.0.0)

## Logging

Logs are written to:
- Console output
- `logs/app.log`: Application logs
- `logs/error.log`: Error logs

Log files are automatically rotated when they reach 10MB.

## CI/CD

The project includes a GitHub Actions workflow that:
1. Runs tests
2. Performs code quality checks
3. Builds and pushes Docker images (on main branch)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Security

- All API endpoints are protected with proper input validation
- Environment variables are used for sensitive configuration
- Docker container runs as non-root user
- Regular security updates through dependency management

## Monitoring

The application includes:
- Health check endpoint
- Request timing headers
- Comprehensive logging
- Error tracking
- Performance monitoring

## Support

For support, please open an issue in the GitHub repository.

## Project Structure

```
contract-features/
├── app/                    # Application source code
├── data/                   # Data files (CSV, JSON)
├── tests/                  # Test files
├── scripts/               # Utility scripts
├── logs/                  # Application logs
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
└── README.md             # Project documentation
``` 