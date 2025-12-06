import json
import time
import logging

from bs4 import BeautifulSoup
from helpers.general_utils import decode_and_soup
from camoufox.sync_api import Camoufox
from curl_cffi import requests


def get_hotel_price_details(target_url, cookie_string, payload, hotel_session):
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": cookie_string,
    }
    price_details = hotel_session.post(target_url, data=payload, headers=headers)
    price_details_json = price_details.json()
    return price_details_json


def get_hotel_price_grid(target_url, cookie_string, payload, hotel_session):
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": cookie_string,
    }
    response = hotel_session.post(target_url, data=payload, headers=headers)
    if response.status_code != 200:
        logging.info(f"Failed to fetch price grid: {response.status_code}")
        return None
    response_json = response.json()
    price_html = response_json["pricegrid"]
    return price_html


def get_hotels(target_url, base_url):
    i = 0
    session = requests.Session()
    session.impersonate = "chrome120"
    impersonation = ["chrome", "firefox"]
    while i < len(impersonation):
        resp = session.get(target_url)
        resp_soup = BeautifulSoup(resp.text, "lxml")
        hotel_list = resp_soup.find_all("div", class_="sr-acco")
        if hotel_list:
            break
        session.impersonate = impersonation[i]
        i += 1
    hotel_links = []
    for hotel in hotel_list:
        hotel_link = hotel.find("a")["href"]
        hotel_links.append(f"{base_url}{hotel_link}")
    logging.info(hotel_links)
    # print(len(hotel_list))
    return hotel_links


def get_hotel_cookies(hotel_link):
    with Camoufox(humanize=True, headless=True) as browser:
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            screen={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        page.goto(hotel_link)
        page.wait_for_selector("#pricegrid", state="attached")
        page.locator("#pricegrid").scroll_into_view_if_needed()
        page.wait_for_selector("#prijzen", state="visible")
        page.locator("#prijzen").scroll_into_view_if_needed()
        time.sleep(2)
        # get cookies
        cookies = context.cookies()
        # Convert cookies (list of dicts) to cookie string
        cookie_string = "; ".join(
            [f"{cookie['name']}={cookie['value']}" for cookie in cookies]
        )
        html = page.content()
        return cookie_string, html


def get_departure_options(price_grid_soup):
    get_departure_options = price_grid_soup.find("span", class_="departure-from")
    get_departure_options = get_departure_options.find_all("input")
    departure_options = [
        {"name": input.find_next("label").text, "code": input["value"]}
        for input in get_departure_options
        if input["value"] != ""
    ]
    return departure_options


def get_date_options(price_grid_soup):
    get_date_options = price_grid_soup.find(
        "select", id="pricegridselectDropdownDepartureDate"
    )
    get_date_options = get_date_options.find_all("option")
    date_options = [
        {"text": option.text, "value": option["value"]}
        for option in get_date_options
        if option["value"] != ""
    ]
    return date_options


def get_trip_options(price_details_json):
    hotel_info = {}
    price_grid_soup = decode_and_soup(price_details_json["pricegrid"])
    price_per_person = (
        price_grid_soup.find("span", class_="price-per-person").get_text().strip()
    )
    decoded_price_per_person = price_per_person.encode("utf-8").decode("unicode_escape")
    label = price_grid_soup.find("td", string="Toeristenbelasting")
    tourist_tax = label.find_next("td", class_="prices").get_text(strip=True)
    hotel_info["final_price_per_person"] = decoded_price_per_person.split()[1]
    hotel_info["currency"] = (
        decoded_price_per_person.split()[0].encode("latin1").decode("utf-8")
    )
    hotel_info["meal_plan"] = (
        price_grid_soup.find("span", id="pricegridselectValueBoardType")
        .get_text()
        .strip()
    )
    hotel_info["tourist_tax"] = tourist_tax
    g4entry = json.loads(price_details_json["ga4Entry"])["GA4"]["ecommerce"]
    flight_details = g4entry["items"][1]
    price_jump = json.loads(price_details_json["priceJump"])["GA4"]["priceJump"]
    # print(g4entry)
    # quit()
    hotel_info["room_name"] = g4entry["items"][0].get("item_variant", "")
    hotel_info["duration"] = (
        f"{g4entry.get('duration_days', '')} days / {g4entry.get('duration_nights', '')} nights"
    )
    hotel_info["departure_date"] = g4entry.get("departure_date", "")
    hotel_info["return_date"] = g4entry.get("return_date", "")
    hotel_info["flight_departure_time"] = flight_details.get(
        "departure_time_outbound", ""
    )
    hotel_info["flight_arrival_time"] = flight_details.get("arrival_time_outbound", "")
    hotel_info["flight_airline"] = price_jump.get("carrier", "")
    return hotel_info


def get_masterdata_id(hotel_soup):
    price_grid_section = hotel_soup.find("section", class_="pricegrid")
    target_element = price_grid_section.find("section", class_="wd-remove")
    master_entity_type = target_element["data-viewedobjectmasterdatatype"]
    master_entity_id = target_element["data-viewedobjectmasterdataid"]
    payload = f"{master_entity_type}_{master_entity_id}"
    return payload


def get_hotel_basic_info(hotel_soup):
    hotel_info = {
        "hotel_name": "",
        "hotel_stars": "",
    }
    hotel_info_container = hotel_soup.find("div", class_="ttl2")
    if not hotel_info_container:
        return hotel_info
    hotel_name = hotel_info_container.find("h1").get_text().strip()
    hotel_info["hotel_name"] = hotel_name

    star_elements = hotel_info_container.find_all("span")
    if not star_elements:
        return hotel_info
    try:
        hotel_stars = star_elements[1]["class"][1].replace("star", "")[0]
        hotel_info["hotel_stars"] = hotel_stars
        hotel_info["accomodation_type"] = "Hotel"
    except Exception as e:
        logging.error(f"Error extracting stars for {hotel_name}: {e}")
        hotel_info["accomodation_type"] = star_elements[0].get_text().strip()

    return hotel_info
