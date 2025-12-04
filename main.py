import json
import time
import html

from camoufox.sync_api import Camoufox
from curl_cffi import requests
from bs4 import BeautifulSoup

class Collector:
    def __init__(self):
        self.base_url = "https://www.tui.nl"
        self.target_url = "https://www.tui.nl/reizen/spanje/formentera/"
        # self.headers = {
        #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        #     'accept-language': 'en-US,en;q=0.9',
        #     'cache-control': 'max-age=0',
        #     'priority': 'u=0, i',
        #     'sec-ch-ua': '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        #     'sec-ch-ua-mobile': '?0',
        #     'sec-ch-ua-platform': '"Windows"',
        #     'sec-fetch-dest': 'document',
        #     'sec-fetch-mode': 'navigate',
        #     'sec-fetch-site': 'same-origin',
        #     'sec-fetch-user': '?1',
        #     'upgrade-insecure-requests': '1',
        #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        # }
        proxies={
        }
        self.session = requests.Session(proxies=proxies)
        self.session.impersonate = "chrome120"
        # print(self.session.get("https://httpbin.org/ip").text)
        # inject session with cookies
        # self.session.get(self.base_url, impersonate="chrome")
    
    def run_pipeline(self):
        hotel_links = self.get_hotels()
        for hotel_link in hotel_links:
            hotel_session = requests.Session()
            date_options = []
            departure_options = []
            hotel_name = hotel_link.split("/")[-2]
            # hotel_details = self.session.get(hotel_link)
            # quit()
            time.sleep(5)
            cookie_string, price_grid_html = self.get_hotel_cookies(hotel_link)
            print(cookie_string)
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
                "Cookie": cookie_string,
            }
            price_grid_soup = BeautifulSoup(price_grid_html, "lxml")
            get_date_options = price_grid_soup.find("select", id="pricegridselectDropdownDepartureDate")
            get_date_options = get_date_options.find_all("option")
            get_departure_options = price_grid_soup.find("span", class_="departure-from")
            get_departure_options = get_departure_options.find_all("input")
            date_options = [option["value"] for option in get_date_options if option["value"] != ""]
            departure_options = [input["value"] for input in get_departure_options if input["value"] != ""]
            payload_extension = self.get_masterdata_id(price_grid_soup)
            for departure_option in departure_options:
                price_payload = f"DepartureFrom={departure_option}&DepartureDate={date_options[1]}&IsSale=false&Destination=Spanje&Entity=-1_{payload_extension}"
                print(price_payload)
                response = hotel_session.post("https://www.tui.nl/data/pricegrid/changepref/", data=price_payload, headers=headers)
                if response.status_code != 200:
                    print(f"Failed to fetch price grid for {hotel_name} with departure {departure_option}")
                    print(response.text)
                    continue
                # print(response.text)
                response_json = response.json()
                price_html = response_json["pricegrid"]
                decoded_price_html = html.unescape(price_html)
                # print(decoded_price_html)
                # 2. Parse with BeautifulSoup
                decoded_price_soup = BeautifulSoup(decoded_price_html, "lxml")
                lowest_price_tag = decoded_price_soup.find("span", string="Laagste")
                if not lowest_price_tag:
                    print(f"No lowest price found for {hotel_name} with departure {departure_option}")
                    continue
                lowest_price_button = lowest_price_tag.find_parent("button")
                lowest_price = lowest_price_button.get_text().replace("Laagste", "").strip()
                price_selection_id = lowest_price_button["rev"]
                selected_price = f"{lowest_price}+Laagste"
                selected_price_payload = f"PriceSelectionId={price_selection_id}&SelectedPrice={selected_price}&IsPricePerPerson=True&IsSale=false&Destination=Spanje&Entity=-1_{payload_extension}"
                price_details = hotel_session.post("https://www.tui.nl/data/pricegrid/priceselect/", data=selected_price_payload, headers=headers)
                with open(f"output/raw_json/{hotel_name}_{departure_option}_price_details.json", "w", encoding="utf-8") as file:
                    json.dump(price_details.json(), file, indent=4)
                with open(f"output/raw_html/{hotel_name}_{departure_option}.html", "w", encoding="utf-8") as file:
                    file.write(decoded_price_html)
                with open(f"output/txt_output/{hotel_name}_{departure_option}.txt", "w", encoding="utf-8") as file:
                    file.write(f"Hotel: {hotel_name}, Departure: {departure_option}, Lowest Price: {lowest_price if lowest_price else 'N/A'}, Price Selection ID: {price_selection_id}, selected_price: {selected_price}")
                print(f"Hotel: {hotel_name}, Departure: {departure_option}, Lowest Price: {lowest_price if lowest_price else 'N/A'}, Price Selection ID: {price_selection_id}, selected_price: {selected_price}")
                time.sleep(5)
                # quit()
            # with open(f"raw_html/{hotel_name}.html", "w", encoding="utf-8") as file:
            #     file.write(hotel_details.text)
            time.sleep(5)


    def get_hotel_cookies(self, hotel_link):
        with Camoufox(humanize=True) as browser:
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                screen={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            page.goto(hotel_link)
            time.sleep(10)
            page.wait_for_selector("#pricegrid", state="attached")
            page.locator("#pricegrid").scroll_into_view_if_needed()
            page.wait_for_selector("#prijzen", state="visible")
            page.locator("#prijzen").scroll_into_view_if_needed()
             # get cookies
            cookies = context.cookies()
            # Convert cookies (list of dicts) to cookie string
            cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            html = page.content()
            return cookie_string, html

    def get_hotels(self):
        i = 0
        impersonation = ["chrome", "firefox", "edge", "safari"]
        while i < len(impersonation):
            resp = self.session.get(self.target_url)
            resp_soup = BeautifulSoup(resp.text, "lxml")
            hotel_list = resp_soup.find_all("div", class_="sr-acco")
            if hotel_list:
                break
            self.session.impersonate = impersonation[i]
            i += 1
        hotel_links = []
        for hotel in hotel_list:
            hotel_link = hotel.find("a")["href"]
            hotel_links.append(f"{self.base_url}{hotel_link}")
        print(hotel_links)
        # print(len(hotel_list))
        return hotel_links


    def get_masterdata_id(self, hotel_soup):
        price_grid_section = hotel_soup.find("section", class_="pricegrid")
        target_element = price_grid_section.find("section", class_="wd-remove")
        master_entity_type = target_element["data-viewedobjectmasterdatatype"]
        master_entity_id = target_element["data-viewedobjectmasterdataid"]
        # data = {
        #     'masterentitytype': master_entity_type,
        #     'masterentityid': master_entity_id,
        #     'theme': '-1',
        #     'isSale': 'false',
        #     'destination': 'Spanje',
        #     'firstview': 'true',
        # }
        payload = f"{master_entity_type}_{master_entity_id}"
        return payload


    def scroll_to_bottom(self, page, pause=800):
        last_height = page.evaluate("document.body.scrollHeight")
        while True:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(pause)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

if __name__ == "__main__":
    collector = Collector()
    collector.run_pipeline()
    # hotel_list = collector.get_hotels()
    # with open("raw.json", "w", encoding="utf-8") as file:
    #     # file.write(hotel_list)
    #     json.dump(hotel_list, file, indent=4)