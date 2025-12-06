import json
import time
import logging

from curl_cffi import requests
from bs4 import BeautifulSoup
from extractor.hotel_extractor import (
    get_trip_options,
    get_departure_options,
    get_date_options,
    get_hotel_basic_info,
    get_masterdata_id,
    get_hotel_cookies,
    get_hotels,
    get_hotel_price_grid,
    get_hotel_price_details,
)
from helpers.general_utils import decode_and_soup

# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )

class Crawl:
    def __init__(self, month_count=0):
        self.month_count = month_count
        self.pref_change_url = "https://www.tui.nl/data/pricegrid/changepref/"
        self.price_select_url = "https://www.tui.nl/data/pricegrid/priceselect/"

    def crawl_hotels(self, hotel_link):
        hotel_data = []
        date_options = []
        departure_options = []
        hotel_name = hotel_link.split("/")[-2]
        hotel_info = {
            "hotel_url": hotel_link,
            "hotel_name": "",
            "hotel_stars": "",
        }
        hotel_session = requests.Session()
        cookie_string, price_grid_html = get_hotel_cookies(hotel_link)
        price_grid_soup = BeautifulSoup(price_grid_html, "lxml")
        date_options = get_date_options(price_grid_soup)
        departure_options = get_departure_options(price_grid_soup)
        payload_extension = get_masterdata_id(price_grid_soup)
        hotel_basic_info = get_hotel_basic_info(price_grid_soup)
        hotel_info.update(hotel_basic_info)
        month_count = self.month_count if self.month_count else len(date_options)
        for departure_option in departure_options:
            hotel_info["departure_airport"] = departure_option["name"]
            for date_option in date_options[:month_count]:
                hotel_info.update(
                    {
                        "room_name": "",
                        "meal_plan": "",
                        "duration": "",
                        "flight_departure_time": "",
                        "flight_arrival_time": "",
                        "flight_airline": "",
                        "final_price_per_person": "",
                        "tourist_tax": "",
                        "departure_month": "",
                        "currency": "",
                        "departure_date": "",
                        "return_date": "",
                        "additional_info": "",
                    }
                )
                logging.info(
                    f"Processing hotel: {hotel_name}, Departure: {departure_option['name']}, Date: {date_option['text'].strip()}"
                )
                hotel_info["departure_month"] = date_option["text"].strip()
                price_payload = f"DepartureFrom={departure_option['code']}&DepartureDate={date_option['value']}&IsSale=false&Destination=Spanje&Entity=-1_{payload_extension}"
                price_html = get_hotel_price_grid(
                    self.pref_change_url,
                    cookie_string,
                    price_payload,
                    hotel_session,
                )

                if not price_html:
                    hotel_info["additional_info"] = "No price grid found"
                    hotel_data.append(hotel_info.copy())
                    logging.info(
                        f"Failed to fetch price grid for {hotel_name} with departure {departure_option['name']} anda date {date_option['text']}"
                    )
                    # print(response.text)
                    continue

                # 2. Parse with BeautifulSoup
                decoded_price_soup = decode_and_soup(price_html)
                lowest_price_tag = decoded_price_soup.find("span", string="Laagste")

                if not lowest_price_tag:
                    hotel_info["additional_info"] = "No trips found"
                    hotel_data.append(hotel_info.copy())
                    logging.info(
                        f"No lowest price found for {hotel_name} with departure {departure_option['name']}"
                    )
                    continue

                lowest_price_button = lowest_price_tag.find_parent("button")
                lowest_price = (
                    lowest_price_button.get_text().replace("Laagste", "").strip()
                )
                price_selection_id = lowest_price_button["rev"]
                selected_price = f"{lowest_price}+Laagste"
                selected_price_payload = f"PriceSelectionId={price_selection_id}&SelectedPrice={selected_price}&IsPricePerPerson=True&IsSale=false&Destination=Spanje&Entity=-1_{payload_extension}"
                price_details_json = get_hotel_price_details(
                    self.price_select_url,
                    cookie_string,
                    selected_price_payload,
                    hotel_session,
                )

                trip_options = get_trip_options(price_details_json)
                hotel_info.update(trip_options)
                hotel_data.append(hotel_info.copy())

                # debug line
                # with open(f"output/raw_json/{hotel_name}_{departure_option['code']}_price_details.json", "w", encoding="utf-8") as file:
                #     json.dump(price_details_json, file, indent=4)
                # with open(f"output/raw_html/{hotel_name}_{departure_option['code']}_{date_option['text'].strip()}.html", "w", encoding="utf-8") as file:
                #     file.write(decoded_price_soup.prettify())
                # with open(f"output/txt_output/{hotel_name}_{departure_option['code']}_{date_option['text'].strip()}.txt", "w", encoding="utf-8") as file:
                #     file.write(f"Hotel: {hotel_name}, Departure: {departure_option['code']}, Lowest Price: {lowest_price if lowest_price else 'N/A'}, Price Selection ID: {price_selection_id}, selected_price: {selected_price}")
                logging.info(
                    f"Hotel: {hotel_name}, Departure: {departure_option['code']}, Lowest Price: {lowest_price if lowest_price else 'N/A'}, Price Selection ID: {price_selection_id}, selected_price: {selected_price}"
                )

        return hotel_data