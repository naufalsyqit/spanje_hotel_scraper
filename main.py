import json
import logging
import asyncio

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
        self.max_workers = 5  # Default max workers for ThreadPoolExecutor if not set

    async def run_pipeline_async(self):
        logging.info("Starting async pipeline run with 10 concurrent workers")
        logging.info("collect hotel links")
        hotel_links = get_hotels(self.target_url, self.base_url)
        hotel_final_data = []
        
        # Create semaphore to limit to 10 concurrent crawls
        semaphore = asyncio.Semaphore(10)
        
        async def crawl_with_semaphore(hotel_link):
            async with semaphore:
                try:
                    hotel_data = await self.crawl.crawl_hotels(hotel_link)
                    logging.info(f"Successfully processed: {hotel_link}")
                    return hotel_data
                except Exception as e:
                    logging.error(f"Error processing {hotel_link}: {e}")
                    return []
        
        results = await asyncio.gather(*[crawl_with_semaphore(link) for link in hotel_links])
        for result in results:
            hotel_final_data.extend(result)
        
        return hotel_final_data

    def run_pipeline(self):
        return asyncio.run(self.run_pipeline_async())


if __name__ == "__main__":
    month_count = 0  # Set to 0 to scrape all months
    max_workers = 5  # set to 1 to disable multithreading

    collector = Collector(month_count=month_count)
    collector.max_workers = max_workers
    hotel_final_data = collector.run_pipeline()

    with open(
        f"output/tui_formentera_hotel_data_{month_count}_months.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(hotel_final_data, file, indent=4, ensure_ascii=False)
