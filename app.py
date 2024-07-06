"""This code makes requests for Privatbank to get currency.
It takes several arguments, one of which is quantity of days (up to 10),
and other are different currencies in the official ISO 4217 standard for
currencies worldwide.

Returns:
    json: Dictionaty with currencies to Grivna (UAH)
"""
import sys
import asyncio
import logging
import json
import platform
from datetime import date, timedelta
from aiohttp import ClientSession


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s "%(levelname)s / %(message)s"',
    datefmt='[%d/%b/%Y %H:%M:%S]'
)

def check_digit_arg(arg: str, days_flag: bool) -> tuple[int, bool]:
    """Validates and processes a numeric argument for days.

    This function checks if the provided numeric argument is within the allowed
    limit (10 days). If valid, it updates the `days_flag` to indicate that a
    valid numeric argument has been processed.

    Args:
        arg (str): The numeric argument as a string.
        days_flag (bool): A flag indicating whether a valid numeric argument
            has already been processed.

    Returns:
        tuple[int, bool]: A tuple containing the number of days (int) and the
            updated days_flag (bool).

    Raises:
        SystemExit: If the numeric argument is greater than 10 or if a numeric
            argument has already been processed.
    """
    if not days_flag:
        days = int(arg)
        if days <= 10:
            days_flag = True
            return days, days_flag

        print('Only 10 days max allowed.')
        sys.exit()
    else:
        print('Too many digit arguments.')
        sys.exit()

def processing_arguments(filtered_currencies, days = 1) -> tuple[int, set]:
    """Processes command line arguments to extract a numeric value for days
    and a set of currency codes.

    This function iterates through command line arguments, identifies numeric
    arguments and currency codes. It ensures only one numeric argument is
    processed and it does not exceed 10 days. All non-numeric arguments are
    added to a set of currency codes.

    Args:
        filtered_currencies (set): A set to store the currency codes.
        days (int, optional): The initial number of days. Default is 1.

    Returns:
        tuple[int, set]: A tuple containing the number of days (int) and
            the set of currency codes (set).
    """
    if len(sys.argv) >= 2:
        args = sys.argv[1:]
        days_flag = False

        for arg in args:
            logging.debug('processing_arguments: %s', arg)

            if arg.isdigit():
                days, days_flag = check_digit_arg(arg, days_flag)
            else:
                filtered_currencies.add(arg.upper())

    return days, filtered_currencies

def format_data(row_data: list, filtered_currencies: set) -> dict:
    """Formats the exchange rate data for specified currencies.

    This function processes a list of exchange rate data and filters it based on
    the provided set of currencies. It returns a dictionary with the date as the
    key and the formatted exchange rate data for the specified currencies.

    Args:
        row_data (dict): A dictionary containing the exchange rate data for
            a specific date.
            Example format:
            {'date': '06.07.2024', 'bank': 'PB', 'baseCurrency': 980,
            'baseCurrencyLit': 'UAH', 'exchangeRate': [{'baseCurrency': 'UAH',
            'currency': 'AUD', 'saleRateNB': 27.2833, 'purchaseRateNB': 27.283},
            {'baseCurrency': 'UAH', 'currency': 'XAU', 'saleRateNB': 95621.19,
            'purchaseRateNB': 95621.19}]}

        filtered_currencies (set): A set of currency codes to filter the data.
            Example: {"USD", "EUR"}

    Returns:
        dict: A dictionary with the date as the key and the filtered exchange
            rate data as the value.
            Example format:
            {
                "2023-07-06": {
                    "USD": {
                        "sale": 27.0,
                        "purchase": 26.5
                    },
                    "EUR": {
                        "sale": 31.0,
                        "purchase": 30.5
                    }
                }
            }
    """
    formatted_data = {}
    for i in row_data['exchangeRate']:
        if i['currency'] in filtered_currencies:
            formatted_data[i['currency']] = {
                'sale': round(
                    float(i.get('saleRate') or i.get('saleRateNB')),
                    2
                ),
                'purchase': round(
                    float(i.get('purchaseRate') or i.get('purchaseRateNB')),
                    2
                )
            }
    return {row_data['date']: formatted_data}

def form_result(dicts: list, filtered_currencies: set) -> list:
    """Formats a list of exchange rate data dictionaries.

    This function processes a list of dictionaries containing exchange rate data
    for different dates and filters it based on the provided set of currencies.
    It uses the `format_data` function to format each dictionary and collects
    the results in a list.

    Args:
        dicts (list): A list of dictionaries, each containing exchange rate data
            for a specific date.
            Example format:
            [
                {
                    "date": "2023-07-06",
                    "exchangeRate": [
                        {
                            "currency": "USD",
                            "saleRate": 27.0,
                            "purchaseRate": 26.5,
                            "saleRateNB": 27.2,
                            "purchaseRateNB": 26.7
                        },
                        ...
                    ]
                },
                ...
            ]
        filtered_currencies (set): A set of currency codes to filter the data.
            Example: {"USD", "EUR"}

    Returns:
        list: A list of dictionaries, each containing formatted exchange rate
            data for the specified currencies and dates.
            Example format:
            [
                {
                    "2023-07-06": {
                        "USD": {
                            "sale": 27.0,
                            "purchase": 26.5
                        },
                        "EUR": {
                            "sale": 31.0,
                            "purchase": 30.5
                        }
                    }
                },
                ...
            ]
    """
    resulted_list = []

    for result in dicts:
        logging.debug('form_result: %s', result)
        formatted_result = format_data(result, filtered_currencies)
        resulted_list.append(formatted_result)

    return resulted_list

async def request(day) -> list:
    """Fetches exchange rate data from the PrivatBank API for a specified date.

    This function sends an asynchronous GET request to the PrivatBank API to
    retrieve exchange rate data for the given date. It logs the response status
    and content type, and returns the response data as a dictionary.

    Args:
        day (str): The date for which to fetch exchange rate data, formatted
            as 'DD.MM.YYYY'.

    Returns:
        dict: The exchange rate data for the specified date.
            Example format:
            {
                "date": "06.07.2023",
                "bank": "PB",
                "baseCurrency": 980,
                "baseCurrencyLit": "UAH",
                "exchangeRate": [
                    {
                        "baseCurrency": "UAH",
                        "currency": "USD",
                        "saleRateNB": 27.2,
                        "purchaseRateNB": 26.7,
                        "saleRate": 27.0,
                        "purchaseRate": 26.5
                    },
                    ...
                ]
            }
    """
    async with ClientSession() as session:
        async with session.get(
            f'https://api.privatbank.ua/p24api/exchange_rates?json&date={day}'
        ) as response:
            logging.debug("request: Status: %s", response.status)
            logging.debug("request: %s", response.headers['content-type'])

            result = await response.json()
            return result

async def main() -> list:
    """Executes the main logic to fetch and format exchange rate data.

    This function processes command line arguments to determine the number of
    days for which to fetch exchange rate data. It then creates asynchronous
    tasks to fetch data for each day and gathers the results using
    `asyncio.gather()`. Finally, it formats the fetched data based on specified
    currencies and returns the formatted results.

    Returns:
        list: A list of dictionaries, each containing formatted exchange rate
            data for the specified currencies and dates.
            Example format:
            [
                {
                    "2023-07-06": {
                        "USD": {
                            "sale": 27.0,
                            "purchase": 26.5
                        },
                        "EUR": {
                            "sale": 31.0,
                            "purchase": 30.5
                        }
                    }
                },
                ...
            ]
    """
    filtered_currencies: set = {'USD', 'EUR'}
    today = date.today()
    days, filtered_currencies = processing_arguments(filtered_currencies)

    tasks = []
    for i in range(days):
        needed_day = (today - timedelta(i)).strftime("%d.%m.%Y")
        tasks.append(request(needed_day))

    results = await asyncio.gather(*tasks)

    return form_result(results, filtered_currencies)


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Start
    print("Requesting data...")
    # Main loop
    currencies = asyncio.run(main())
    # Results
    print(
        "Results of request to Privatbank:\n",
        json.dumps(currencies, indent=2)
    )
