import requests
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import threading

API_KEY = "c911deded97311d0bbd5b39e6381089636b49bda88b4b37b3911f81e26b4ffe1"
API_URL = "https://benyehuda.org/api/v1/search"
OUT_DIR = Path("output/benyehuda_modern_texts")
OUT_DIR.mkdir(exist_ok=True)

session = requests.Session()  # reuse connections

# concurrency cap for downloads
MAX_CONCURRENT_DOWNLOADS = 5
download_semaphore = threading.Semaphore(MAX_CONCURRENT_DOWNLOADS)


def request_with_retry(method, url, **kwargs):
    """Generic HTTP request with retries + exponential backoff."""
    max_retries = kwargs.pop("max_retries", 5)
    backoff_base = kwargs.pop("backoff_base", 1.5)

    for attempt in range(max_retries):
        try:
            r = session.request(method, url, **kwargs)
            if r.status_code == 429:  # rate-limited
                retry_after = int(r.headers.get("Retry-After", 2))
                time.sleep(retry_after)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            sleep_time = backoff_base ** attempt + random.random()
            time.sleep(sleep_time)
            if attempt == max_retries - 1:
                raise e
    return None


def search_period(period="modern", search_after=None):
    payload = {
        "key": API_KEY,
        "periods": [period],
        "view": "basic",
        "file_format": "txt",
    }
    if search_after:
        payload["search_after"] = search_after
    r = request_with_retry("POST", API_URL, json=payload)
    return r.json() if r else {}


def download_work(work):
    """Download one work from its download_url and write metadata as first row."""
    metadata = work.get("metadata", {})
    title = metadata.get("title")
    work_id = work.get("id")
    download_url = work.get("download_url")
    if not download_url:
        return

    safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_")).rstrip()
    filename = OUT_DIR / f"{work_id}_{safe_title}.txt"

    if filename.exists():
        return

    with download_semaphore:
        r = request_with_retry("GET", download_url)
        if not r:
            return
        text = r.content.decode("utf-8")

    meta_row = (
        "author\torig_lang\tgenre\traw_publication_date\n"
        f"{metadata.get('author','')}\t{metadata.get('orig_lang','')}\t"
        f"{metadata.get('genre','')}\t{metadata.get('raw_publication_date','')}\n"
    )

    filename.write_text(meta_row + text, encoding="utf-8")


def main():
    search_after = None
    total = 0

    # Initial request to get total count
    data = search_period(search_after=search_after)
    total_count = data.get("total_count", 0)

    with tqdm(total=total_count, desc="Downloading works") as pbar:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []

            while True:
                works = data.get("data", [])
                for w in works:
                    futures.append(executor.submit(download_work, w))

                # process finished downloads while we continue searching
                for f in as_completed(futures[:]):
                    if f.done():
                        try:
                            f.result()
                        except Exception as e:
                            print(f"Download failed: {e}")
                        futures.remove(f)
                        total += 1
                        pbar.update(1)

                search_after = data.get("next_page_search_after")
                if not search_after:
                    break
                data = search_period(search_after=search_after)

            # wait for remaining downloads
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    print(f"Download failed: {e}")
                total += 1
                pbar.update(1)

    print(f"Finished. Downloaded {total} modern works into {OUT_DIR}")


if __name__ == "__main__":
    main()
