# Currency Transfer Rules API

## Overview
This project is a FastAPI-based application that provides an API for querying provider's money-transfer rules. 
It includes functionality for currency conversion, exchange rate management, and transfer rule querying.

## Features
- Transfer rule querying
- Admin panel for data management
- Transfer provider management

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
  - Description: The name of the PostgreSQL database to be used by the application.
  - Example: POSTGRES_DB=transfer_rules_db
  - Explanation: This is the database where all your application data will be stored. Choose a name that's relevant to your project.
- `POSTGRES_USER=<your_postgres_user>`
  - Description: The username for connecting to the PostgreSQL database.
  - Example: POSTGRES_USER=transfer_admin
  - Explanation: This user should have sufficient privileges to create, read, update, and delete data in the specified database.
- `POSTGRES_PASSWORD=<your_postgres_password>`
  - Description: The password for the PostgreSQL user.
  - Example: POSTGRES_PASSWORD=secure_password_123
  - Explanation: Choose a strong, unique password. Never use default or easily guessable passwords in a production environment.
- `POSTGRES_POOL_SIZE=<your_postgres_pool_size>`
  - Description: The maximum number of connections to keep in the database pool.
  - Example: POSTGRES_POOL_SIZE=10
  - Explanation: This helps manage database connections efficiently. A higher number allows more concurrent connections but consumes more resources.
- `POSTGRES_MAX_OVERFLOW=<your_postgres_max_overflow>`
  - Description: The maximum number of connections that can be created beyond the pool size.
  - Example: POSTGRES_MAX_OVERFLOW=20
  - Explanation: This allows for handling sudden spikes in database connection requests beyond the normal pool size.
- `POSTGRES_ECHO=<True_or_False>` (Use only if database echo for debug is needed)
  - Description: Whether SQLAlchemy should echo all SQL statements to the console.
  - Example: POSTGRES_ECHO=False
  - Explanation: Set to True for debugging database queries. Keep False in production to avoid logging sensitive information.

### Application Configuration:
- `APP_RUN_HOST=<your_app_run_host>`
  - Description: The host address on which the FastAPI application will run.
  - Example: APP_RUN_HOST=0.0.0.0
  - Explanation: Use 0.0.0.0 to make the app accessible on all network interfaces, or 127.0.0.1 for local-only access.
- `APP_RUN_PORT=<your_app_run_port>`
  - Description: The port number on which the FastAPI application will listen.
  - Example: APP_RUN_PORT=8000
  - Explanation: Choose an available port. Common choices are 8000, 8080, 5050 or 5000 for development.
- `DEBUG=<True_or_False>`
  - Description: Enables or disables debug mode for the application.
  - Example: DEBUG=False <- value by default
  - Explanation: Set to True during development for detailed error messages. Always set to False in production.

### SQLAdmin Configuration:
- `SQLADMIN_SECRET_KEY=<your_sqladmin_secret_key>`
  - Description: Secret key used for securing the SQLAdmin interface.
  - Example: SQLADMIN_SECRET_KEY=your_very_long_and_secure_random_string
  - Explanation: This should be a long, random string. It's crucial for the security of the admin interface.
- `SQLADMIN_USERNAME=<your_sqladmin_username>`
  - Description: Username for accessing the SQLAdmin interface.
  - Example: SQLADMIN_USERNAME=admin
  - Explanation: Choose a non-obvious username. Avoid common choices like 'admin' in production.
- `SQLADMIN_PASSWORD=<your_sqladmin_password>`
  - Description: Password for accessing the SQLAdmin interface.
  - Example: SQLADMIN_PASSWORD=very_secure_admin_password
  - Explanation: Use a strong, unique password. This is crucial for protecting your admin interface.

### Cache Configuration:
- `USD_CURRENCY_CACHE_SEC=<cache_duration_in_seconds>`
  - Description: Duration (in seconds) for caching USD currency data.
  - Example: USD_CURRENCY_CACHE_SEC=1800
  - Explanation: This sets how long USD currency data is cached before being refreshed. 1800 seconds = 30 minutes.
- `OBJECTS_CACHE_SEC=<cache_duration_in_seconds>`
  - Description: Duration (in seconds) for caching other object data (used for main api endpoint's service).
  - Example: OBJECTS_CACHE_SEC=600
  - Explanation: This sets the cache duration for other frequently accessed objects. 600 seconds = 10 minutes.  - 

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
- Get all exchange rates: `GET /api/all-exchange-rates`
- Get a specific exchange rate: `GET /api/exchange-rate/{exchange_rate_id}`

For all endpoints that require an ID, you'll need to provide the UUID of the item you're looking for. 
The API will return detailed information about the requested item or a list of items, depending on the endpoint.

## Swagger UI Documentation
For an interactive API documentation experience, you can access the Swagger UI by navigating to `/docs` in your browser
when the application is running. This provides a user-friendly interface to explore and test all available endpoints.

## Admin Panel
The admin panel is available at `/admin`. Use the credentials specified in the `.env` file to log in.


## Contact
Written by Ivan Aleksandrovskii Email: i.aleksandrovskii@chrona.ai