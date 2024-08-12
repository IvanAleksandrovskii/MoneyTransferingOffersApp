def format_exchange_rate(model, name):
    return f"{model.provider.name} - {model.from_currency.abbreviation} - {model.to_currency.abbreviation}"
