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

def processing_arguments(filtered_currencies, days = 1) -> int:
    """This function processes command line arguments.

    Returns:
        int: Quantity of days to show.
        set: Set of currencies to show.
    """
    if len(sys.argv) >= 2:
        args = sys.argv[1:]
        days_flag = False
        for arg in args:
            logging.debug(arg)
            if arg.isdigit():
                if not days_flag:
                    days = int(arg)
                    if days <= 10:
                        days_flag = True
                    else:
                        print('Only 10 days max allowed.')
                        sys.exit()
                else:
                    print('Too many digit arguments.')
                    sys.exit()
            else:
                filtered_currencies.add(arg.upper())

    return days, filtered_currencies

def format_data(row_data, filtered_currencies) -> dict:
    formatted_data = {}
    for i in row_data['exchangeRate']:
        if i['currency'] in filtered_currencies:
            formatted_data[i['currency']] = {
                'sale': round(
                    float(
                        i.get('saleRate') or i.get('saleRateNB')
                    ), 2
                ),
                'purchase': round(
                    float(
                        i.get('purchaseRate') or i.get('purchaseRateNB')
                    ), 2
                )
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
    filtered_currencies: set = {'USD', 'EUR'}
    today = date.today()
    days, filtered_currencies = processing_arguments(filtered_currencies)

    tasks = []
    for i in range(days):
        needed_day = (today - timedelta(i)).strftime("%d.%m.%Y")
        tasks.append(request(needed_day))

    results = await asyncio.gather(*tasks)

    resulted_list = []

    for result in results:
        logging.debug(result)
        formatted_result = format_data(result, filtered_currencies)
        resulted_list.append(formatted_result)

    return resulted_list


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    currencies = asyncio.run(main())
    print(
        "Results of request to Privatbank:\n",
        json.dumps(currencies, indent=2)
    )
