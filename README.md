# Product API

A simple FastAPI application to manage products and their offers.

## Installation

### Clone the Repository

```bash
git clone https://github.com/yourusername/product-api.git
cd product-api
```
### Install dependencies
```bash
pipenv install
```

### Setup ENV variables in Dockerfile
```bash
cp Docker_example Docker
```
edit env variables

## Run

### From docker
```bash
docker build -t product-api .
docker-compose up --build
```

### Locally
```bash
pipenv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```