def format_exchange_rate(model, name):
    return f"{model.provider.name} - {model.from_currency.abbreviation} - {model.to_currency.abbreviation}"


# def format_transfer_rule(model, name):
#     return (f"{model.provider.name} - {model.send_country.name} - {model.receive_country.name} - "
#             f"{model.transfer_currency.abbreviation if model.transfer_currency else 'Unknown'} - "
#             f"{model.min_transfer_amount} - {model.max_transfer_amount}")
