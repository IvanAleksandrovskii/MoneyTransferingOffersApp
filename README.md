# Currency Transfer Rules API

## Overview
This project is a FastAPI-based application that provides an API for querying provider's money-transfer rules. 
It includes functionality for currency conversion, exchange rate management, and transfer rule querying.

## Features
- Transfer rule querying
- Admin panel for data management
- Transfer provider management
- Exchange rate tracking

## Technologies Used
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic (for database migrations)
- Pydantic (for data validation)
- Docker

## Prerequisites
- Docker (for containerized deployment)
- Python 3.12+ (for local development, don't forget to change "pg" -> "0.0.0.0" in config file for that case)

## Installation

### Local Setup
1. Clone the repository.

2. Create a `.env` file in the project root or fill in the `docker-compose.yml` file with the required environment variables (see next section).

3. Build and run the Docker containers:
   ```
   docker-compose up --build
   ```

4. The API will be available at `http://localhost:8000` and the admin panel at `http://localhost:8000/admin` (by default configuration).

## Environment Variables

Create a `.env` file or fill in the `docker-compose.yml` file with the following variables:

### PostgreSQL Configuration:
- `POSTGRES_DB=<your_postgres_db>`
- `POSTGRES_USER=<your_postgres_user>`
- `POSTGRES_PASSWORD=<your_postgres_password>`
- `POSTGRES_POOL_SIZE=<your_postgres_pool_size>`
- `POSTGRES_MAX_OVERFLOW=<your_postgres_max_overflow>`
- `POSTGRES_ECHO=<True_or_False>` (Use only if database echo for debug is needed)

### Application Configuration:
- `APP_RUN_HOST=<your_app_run_host>`
- `APP_RUN_PORT=<your_app_run_port>`
- `DEBUG=<True_or_False>`

### SQLAdmin Configuration:
- `SQLADMIN_SECRET_KEY=<your_sqladmin_secret_key>`
- `SQLADMIN_USERNAME=<your_sqladmin_username>`
- `SQLADMIN_PASSWORD=<your_sqladmin_password>`

### Cache Configuration:
- `USD_CURRENCY_CACHE_SEC=<cache_duration_in_seconds>`
- `OBJECTS_CACHE_SEC=<cache_duration_in_seconds>`

## API Documentation

Our API provides several endpoints to help you work with transfer rules, currencies, countries, and providers. 
Here's a breakdown of what you can do (swagger is available, check `/docs`):

### Main Functionality

#### Get Filtered Transfer Rules
- **Endpoint:** `GET /api/transfer-rules-filtered`
- **What it does:** 
  - Fetches transfer rules based on the countries you specify, with optional currency and amount filters.
- **You'll need to provide:**
  - The ID of the sending country
  - The ID of the receiving country
  - Optionally, the ID of the currency you're sending from
  - Optionally, the amount you want to transfer
- **What you'll get back:** 
  - A detailed list of transfer rules that match your criteria, including provider information, fees, and exchange rates.

### Working with Currencies, Countries, and Documents

#### Currencies
- Get details of a specific currency: `GET /api/currency/{currency_id}`
- Get a list of all available currencies: `GET /api/currencies`

#### Countries
- Get details of a specific country: `GET /api/country/{country_id}`
- Get a list of all countries: `GET /api/countries`

#### Documents
- Get details of a specific document: `GET /api/document/{document_id}`
- Get a list of all documents: `GET /api/documents`

### Provider and Transfer Rule Information

#### Providers
- Get a list of all transfer providers: `GET /api/all-providers`
- Get details of a specific provider: `GET /api/provider/{provider_id}`

#### Transfer Rules
- Get all transfer rules: `GET /api/all-transfer-rules`
- Get details of a specific transfer rule: `GET /api/transfer-rule/{transfer_rule_id}`

#### Exchange Rates
- Get all exchange rates (debug purpose): `GET /api/all-exchange-rates`
- Get a specific exchange rate: `GET /api/exchange-rate/{exchange_rate_id}`

For all endpoints that require an ID, you'll need to provide the UUID of the item you're looking for. 
The API will return detailed information about the requested item or a list of items, depending on the endpoint.

If you need more detailed information about the structure of the responses or have any questions about using these 
endpoints, please refer to our detailed API documentation `/docs`.

## Admin Panel
The admin panel is available at `/admin`. Use the credentials specified in the `.env` file to log in.


## Contact
Written by Ivan Aleksandrovskii Email: i.aleksandrovskii@chrona.ai