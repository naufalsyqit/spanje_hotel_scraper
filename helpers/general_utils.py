import html

from bs4 import BeautifulSoup


def decode_and_soup(encoded_html):
    decoded_html = html.unescape(encoded_html)
    decoded_soup = BeautifulSoup(decoded_html, "lxml")
    return decoded_soup
