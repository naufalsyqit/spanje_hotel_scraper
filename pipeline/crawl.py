import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from curl_cffi import requests
from bs4 import BeautifulSoup
from extractor.hotel_extractor import (
    get_trip_options,
    get_departure_options,
    get_date_options,
    get_hotel_basic_info,
    get_masterdata_id,
    get_hotel_cookies,
    get_hotel_price_grid,
    get_hotel_price_details,
    get_hotel_cookies_alt
)
from helpers.general_utils import decode_and_soup


class Crawl:
    def __init__(self, month_count=0):
        self.month_count = month_count
        self.pref_change_url = "https://www.tui.nl/data/pricegrid/changepref/"
        self.price_select_url = "https://www.tui.nl/data/pricegrid/priceselect/"
        self.next_page_url = "https://www.tui.nl/data/pricegrid/gridnavigation/"
        self.limit_weeks = 5
        self.max_workers = 6
    
    def process_price_option(self, price_option, hotel_info, payload_extension, cookie_string, hotel_session):
        """Process a single price option and return hotel data"""
        hotel_data_item = hotel_info.copy()
        hotel_data_item.update(
            {
                "room_name": "",
                "meal_plan": "",
                "duration": "",
                "flight_departure_time": "",
                "flight_arrival_time": "",
                "flight_airline": "",
                "final_price_per_person": "",
                "tourist_tax": "",
                "currency": "",
                "departure_date": "",
                "return_date": "",
            }
        )
        i = 0
        max_limit = 3
        while i < max_limit:
            try:
                selected_price = price_option["selectedprice"]
                price_selection_id = price_option["priceselectionid"]
                selected_price_payload = f"PriceSelectionId={price_selection_id}&SelectedPrice={selected_price}&IsPricePerPerson=True&IsSale=false&Destination=Spanje&Entity=-1_{payload_extension}"
                
                price_details_json = get_hotel_price_details(
                    self.price_select_url,
                    cookie_string,
                    selected_price_payload,
                    hotel_session,
                )
                break
            except Exception as e:
                time.sleep(3)
                logging.error(f"Error processing price option {price_option}: {e}")
                i += 1
        if i == max_limit:
            logging.error(f"Failed to process price option after retries: {price_option}")
            return hotel_data_item  # Return with empty/default values
        trip_options = get_trip_options(price_details_json)
        hotel_data_item.update(trip_options)
        logging.info(f"Processed price option: {selected_price}")
        return hotel_data_item

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
        cookie_string, hotel_basic_html, price_grid_html, hotel_session = get_hotel_cookies_alt(hotel_link)
        price_grid_soup = BeautifulSoup(price_grid_html, "lxml")
        hotel_basic_soup = BeautifulSoup(hotel_basic_html, "lxml")
        date_options = get_date_options(price_grid_soup)
        departure_options = get_departure_options(price_grid_soup)
        payload_extension = get_masterdata_id(hotel_basic_soup)
        hotel_basic_info = get_hotel_basic_info(hotel_basic_soup)
        hotel_info.update(hotel_basic_info)
        month_count = self.month_count if self.month_count else len(date_options)
        for departure_option in departure_options:
            price_grid_found = False
            hotel_info["departure_airport"] = departure_option["name"]
            for date_option in date_options[:month_count]:
                if price_grid_found:
                    break
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
                try:
                    logging.info(
                        f"Processing hotel: {hotel_name}, Departure: {departure_option['name']}, Date: {date_option['text'].strip()}"
                    )
                    # hotel_info["departure_month"] = date_option["text"].strip()
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
                            f"Failed to fetch price grid for {hotel_name} with departure {departure_option['name']} and date {date_option['text']}"
                        )
                        continue
                    limit_weeks = self.limit_weeks
                    while True:
                        price_list = []
                        # 2. Parse with BeautifulSoup
                        decoded_price_soup = decode_and_soup(price_html)
                        get_price_list = decoded_price_soup.find("tr", {"data-cabin-type": "NotSpecified"})
                        if not get_price_list:
                            hotel_info["departure_month"] = date_option['text'].strip()
                            hotel_info["additional_info"] = "No price grid found"
                            hotel_data.append(hotel_info.copy())
                            logging.info("No price list found on this page.")
                            break
                        price_grid_found = True
                        get_price_list = get_price_list.find_all("td")
                        for i in range(1, len(get_price_list)):
                            final_price_button = get_price_list[i].find("button")
                            if not final_price_button:
                                continue
                            final_price = final_price_button.get_text().strip()
                            if "Laagste" in final_price:
                                lowest_price = (
                                final_price.replace("Laagste", "").strip()
                                )
                                price_list.append({"selectedprice": f"{lowest_price}+Laagste", "priceselectionid": final_price_button["rev"]})
                                continue
                            price_list.append({"selectedprice": final_price, "priceselectionid": get_price_list[i].find("button")["rev"]})
                        for price_option in price_list:
                            # print(price_option)
                            logging.info(
                                f"Hotel: {hotel_name}, Departure: {departure_option['code']}, {price_option['selectedprice']}"
                            )
                        
                        # Process price options in parallel using 5 threads
                        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                            futures = [
                                executor.submit(
                                    self.process_price_option,
                                    price_option,
                                    hotel_info,
                                    payload_extension,
                                    cookie_string,
                                    hotel_session
                                )
                                for price_option in price_list
                            ]
                            for future in as_completed(futures):
                                result = future.result()
                                hotel_data.append(result)

                        # debug line
                        # with open(f"output/raw_json/{hotel_name}_{departure_option['code']}_price_details.json", "w", encoding="utf-8") as file:
                        #     json.dump(price_details_json, file, indent=4)
                        # with open(f"output/raw_html/{hotel_name}_{departure_option['code']}_{date_option['text'].strip()}.html", "w", encoding="utf-8") as file:
                        #     file.write(decoded_price_soup.prettify())
                        # with open(f"output/txt_output/{hotel_name}_{departure_option['code']}_{date_option['text'].strip()}.txt", "w", encoding="utf-8") as file:
                        #     file.write(f"Hotel: {hotel_name}, Departure: {departure_option['code']}, Lowest Price: {lowest_price if lowest_price else 'N/A'}, Price Selection ID: {price_selection_id}, selected_price: {selected_price}")

                        # logging.info(
                        #     f"Hotel: {hotel_name}, Departure: {departure_option['code']}, Lowest Price: {lowest_price if lowest_price else 'N/A'}, Price Selection ID: {price_selection_id}, selected_price: {selected_price}"
                        # )
                        if limit_weeks == 1:
                            logging.info("week limit reached, stopping pagination")
                            break
                        check_next = decoded_price_soup.find("button", class_="lnk next-page")
                        if not check_next:
                            break
                        next_payload = f"MoveRelativeDates=later&IsSale=true&Destination=Spanje&Entity=-1_{payload_extension}"
                        price_html = get_hotel_price_grid(
                            self.next_page_url,
                            cookie_string,
                            next_payload,
                            hotel_session,
                        )
                        if not price_html:
                            logging.warning("Failed to fetch next page")
                            break
                        if not limit_weeks:
                            logging.info("No week limit, keep going until the end")
                            continue
                        logging.info(f"Weeks remaining: {limit_weeks - 1}")
                        limit_weeks -= 1
                except Exception as e:
                    logging.error(
                        f"Error processing hotel {hotel_name} with departure {departure_option['name']} and date {date_option['text'].strip()}: {e}", exc_info=True
                    )
                    hotel_info["additional_info"] = "No price grid found"
                    hotel_data.append(hotel_info.copy())

        return hotel_data
