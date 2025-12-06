import json
import logging

from extractor.hotel_extractor import get_hotels
from pipeline.crawl import Crawl

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class Collector:
    def __init__(self, month_count=0):
        logging.info(f"Initializing Collector with month_count={month_count}")
        self.base_url = "https://www.tui.nl"
        self.target_url = "https://www.tui.nl/reizen/spanje/formentera/"
        self.crawl = Crawl(month_count=month_count)

    def run_pipeline(self):
        logging.info("Starting pipeline run")
        logging.info("collect hotel links")
        hotel_links = get_hotels(self.target_url, self.base_url)
        hotel_final_data = []
        for hotel_link in hotel_links:
            hotel_data = self.crawl.crawl_hotels(hotel_link)
            hotel_final_data.extend(hotel_data)
        return hotel_final_data


if __name__ == "__main__":
    month_count = 2  # Set to 0 to scrape all months
    collector = Collector(month_count=month_count)
    hotel_final_data = collector.run_pipeline()

    with open(
        f"output/tui_formentera_hotel_data_{month_count}_months.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(hotel_final_data, file, indent=4, ensure_ascii=False)
