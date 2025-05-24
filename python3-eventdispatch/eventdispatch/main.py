'''
Created on 2025-05-23

@author: Charlie Yan

Copyright (c) 2025, Charlie Yan
License: Apache-2.0 (see LICENSE for details)
'''
import requests

_QUOTE_URL = 'https://quotes.rest/qod'

def get_random_quote():
    """Get a random quote."""

    res = requests.get(_QUOTE_URL)
    return res.json()['contents']['quotes'][0]['quote']

def display_quote():
    """Display a random quote."""

    print(f'My random quote is: "{get_random_quote()}"')

if __name__ == '__main__':
    display_quote()