import json
import logging
import time
import os

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from extractor.hotel_extractor import get_hotels
from pipeline.crawl import Crawl

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
)


class Collector:
    def __init__(self, month_count=0, max_weeks=0):
        logging.info(f"Initializing Collector with month_count={month_count} and max_weeks={max_weeks}")
        self.base_url = "https://www.tui.nl"
        self.target_url = "https://www.tui.nl/reizen/spanje/formentera/"
        self.crawl = Crawl(month_count=month_count)
        self.crawl.limit_weeks = max_weeks
        self.max_workers = 5  # Default max workers for ThreadPoolExecutor if not set

    def run_pipeline(self):
        logging.info("Starting pipeline run")
        logging.info("collect hotel links")
        hotel_links = get_hotels(self.target_url, self.base_url)
        hotel_final_data = []
        logging.info(f"Starting crawling with {self.max_workers} workers")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.crawl.crawl_hotels, link): link
                for link in hotel_links
            }
            for future in as_completed(futures):
                hotel_link = futures[future]
                try:
                    hotel_data = future.result()
                    hotel_final_data.extend(hotel_data)
                    logging.info(f"Successfully processed: {hotel_link}")
                    time.sleep(10)  # Respectful delay between requests
                except Exception as e:
                    logging.error(f"Error processing {hotel_link}: {e}")

        return hotel_final_data


if __name__ == "__main__":
    start_time = time.time()
    logging.info(f"Starting the hotel data extraction process {start_time}")
    month_count = 3  # Set to 0 to check all months
    max_workers = 10  # set to 1 to disable multithreading
    max_weeks = 0 # set to 0 to disable week limit and will scrape the whole available days on weeks

    collector = Collector(month_count=month_count, max_weeks=max_weeks)
    collector.max_workers = max_workers
    hotel_final_data = collector.run_pipeline()
    hotel_final_data = list(set(hotel_final_data))
    datetime_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"output/tui_formentera_hotel_data_{month_count}_months_{datetime_str}.json"

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(hotel_final_data, file, indent=4, ensure_ascii=False)

    end_time = time.time()
    logging.info(f"Hotel data extraction completed in {end_time - start_time} seconds")
