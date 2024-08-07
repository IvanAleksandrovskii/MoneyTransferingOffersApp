APP_RUN_HOST =
APP_RUN_PORT =
DEBUG =

POSTGRES_USER =
POSTGRES_PASSWORD = 
POSTGRES_DB = 

POSTGRES_POOL_SIZE = 
POSTGRES_MAX_OVERFLOW = 

POSTGRES_ECHO = 

SQLADMIN_SECRET_KEY = 
SQLADMIN_USERNAME = 
SQLADMIN_PASSWORD = 


# API Documentation

## Main API Endpoints

### POST /api/transfer-rules-by-countries
- Description: Get transfer rules by countries
- Request body: TransferRuleRequest
- Response: List[List[Any]]

### POST /api/transfer-rules-full-filled-info
- Description: Get detailed transfer rules information
- Request body: TransferRuleFullRequest
- Response: OptimizedTransferRuleResponse

### GET /api/object/{uuid}
- Description: Get object by UUID
- Parameters: uuid (UUID)
- Response: GenericObjectResponse

## Global Objects

### GET /api/global-objects/currency/{currency_id}
- Description: Get currency by ID
- Parameters: currency_id (UUID)
- Response: CurrencyResponse

### GET /api/global-objects/currencies
- Description: Get all currencies
- Response: List[CurrencyResponse]

### GET /api/global-objects/country/{country_id}
- Description: Get country by ID
- Parameters: country_id (UUID)
- Response: CountryResponse

### GET /api/global-objects/countries
- Description: Get all countries
- Response: List[CountryResponse]

## Provider Objects

### GET /api/provider-objects/providers
- Description: Get all providers
- Response: List[ProviderResponse]

### GET /api/provider-objects/provider/{provider_id}/exchange-rates
- Description: Get exchange rates for a specific provider
- Parameters: provider_id (UUID)
- Response: List[ExchangeRateResponse]

### GET /api/provider-objects/exchange-rates
- Description: Get all exchange rates
- Response: List[ExchangeRateResponse]

### GET /api/provider-objects/transfer-rules
- Description: Get all transfer rules
- Response: List[List[Any]]

## By Name Endpoints

### GET /api/by-name/provider/{provider_name}/exchange-rates
- Description: Get exchange rates for a provider by name
- Parameters: provider_name (str)
- Response: List[ExchangeRateResponse]

### GET /api/by-name/currency/{currency_name}
- Description: Get currency by name
- Parameters: currency_name (str)
- Response: CurrencyResponse

### GET /api/by-name/country/{country_name}
- Description: Get country by name
- Parameters: country_name (str)
- Response: CountryResponse
