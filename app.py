"""This code makes requests for Privatbank to get currency.

Returns:
    json: Dictionaty with currencies to Grivna (UAH)
"""
import platform
import asyncio
import logging
import json
from datetime import date, timedelta
from aiohttp import ClientSession


logging.basicConfig(
    level=logging.INFO,
    format='%(name)s - %(asctime)s "%(levelname)s / %(message)s"',
    datefmt='[%d/%b/%Y %H:%M:%S]'
)

def format_data(row_data, filtered_currencies):
    formatted_data = [
        {row_data['date']: {
            rate['currency']: {
                'sale': rate.get('saleRate', rate.get('saleRateNB')),
                'purchase': rate.get('purchaseRate', rate.get('purchaseRateNB'))
            }
            for rate in row_data['exchangeRate']
            if rate['currency'] in filtered_currencies
        }}
    ]
    return json.dumps(formatted_data, indent=2)


async def request(today):
    async with ClientSession() as session:
        async with session.get(
            f'https://api.privatbank.ua/p24api/exchange_rates?json&date={today}'
        ) as response:
            logging.debug("Status: %s", response.status)
            logging.debug("Content-type: %s", response.headers['content-type'])
            logging.debug('Cookies: %s', response.cookies)
            logging.debug(response.ok)
            result = await response.json()
            return result

async def main():
    FILTERED_CURRENCIES = ['USD', 'EUR']
    today = date.today()
    nedded_day = (today - timedelta(days=1)).strftime("%d.%m.%Y")
    result = await request(nedded_day)
    logging.debug(result)
    return format_data(result, FILTERED_CURRENCIES)


if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    r = asyncio.run(main())
    print(r)
