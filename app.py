"""This code makes requests for Privatbank to get currency.

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
    format='%(name)s - %(asctime)s "%(levelname)s / %(message)s"',
    datefmt='[%d/%b/%Y %H:%M:%S]'
)

def processing_arguments() -> int:
    """This function processes command line arguments.

    Returns:
        int: Quantity of days
    """
    try:
        if len(sys.argv) > 2:
            raise IndexError("Too many arguments.")
        days = int(sys.argv[1]) if len(sys.argv) == 2 else 1

    except ValueError:
        print("The argument must be an integer.")
        sys.exit()
    except IndexError as e:
        print(e)
        sys.exit()

    return days

def format_data(row_data, filtered_currencies) -> dict:
    formatted_data = {}
    for i in row_data['exchangeRate']:
        if i['currency'] in filtered_currencies:
            formatted_data[i['currency']] = {
                'sale': i.get('saleRate'),
                'purchase': i.get('purchaseRate')
            }
    return {row_data['date']: formatted_data}


async def request(day) -> list:
    async with ClientSession() as session:
        async with session.get(
            f'https://api.privatbank.ua/p24api/exchange_rates?json&date={day}'
        ) as response:
            logging.debug("Status: %s", response.status)
            logging.debug("Content-type: %s", response.headers['content-type'])
            logging.debug('Cookies: %s', response.cookies)
            logging.debug(response.ok)
            result = await response.json()
            return result

async def main() -> list:
    filtered_currencies = ['USD', 'EUR']
    today = date.today()
    days = processing_arguments()

    resulted_list = []
    for i in range(days):
        needed_day = (today - timedelta(i)).strftime("%d.%m.%Y")
        result = await request(needed_day)
        logging.debug(result)
        formatted_result = format_data(result, filtered_currencies)
        resulted_list.append(formatted_result)

    return resulted_list


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    currencies = asyncio.run(main())
    print("Results of request to Privatbank:")
    print(json.dumps(currencies, indent=2))
