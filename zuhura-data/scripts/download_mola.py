
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit, unquote
from requests.adapters import HTTPAdapter
import requests
import re
import time
from tqdm import tqdm

BASE_URL = (
    "https://pds-geosciences.wustl.edu/"
    "mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/"
)

OUTPUT_DIR = Path("data/raw/mola/meg128")

# Start with 4 workers. Increase to 6 only if the server
# and your internet connection handle it comfortably.
MAX_WORKERS = 4
CHUNK_SIZE = 1024 * 1024
MAX_RETRIES = 3

PATTERN = re.compile(
    r"^megt.*\.(img|lbl|hdr|xml)$",
    re.IGNORECASE
)


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.links.append(value)


def create_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Zuhura-Mars-Data-Downloader/2.0"
    })
    return session


def get_archive_files():
    with create_session() as session:
        response = session.get(BASE_URL, timeout=60)
        response.raise_for_status()

    parser = LinkParser()
    parser.feed(response.text)

    files = set()

    for href in parser.links:
        filename = unquote(
            urlsplit(href).path.rsplit("/", 1)[-1]
        )

        if PATTERN.match(filename):
            files.add(filename)

    return sorted(files)


def download_file(filename):
    destination = OUTPUT_DIR / filename
    temporary = destination.with_name(destination.name + ".part")
    url = urljoin(BASE_URL, filename)

    if destination.exists() and destination.stat().st_size > 0:
        return "skipped", filename

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            existing_size = (
                temporary.stat().st_size
                if temporary.exists()
                else 0
            )

            headers = {}

            if existing_size:
                headers["Range"] = f"bytes={existing_size}-"

            with create_session() as session:
                with session.get(
                    url,
                    headers=headers,
                    stream=True,
                    timeout=(30, 180)
                ) as response:

                    response.raise_for_status()

                    # Append only if the server accepted the range.
                    append = (
                        existing_size > 0
                        and response.status_code == 206
                    )

                    if existing_size > 0 and not append:
                        existing_size = 0

                    mode = "ab" if append else "wb"

                    content_type = response.headers.get(
                        "Content-Type", ""
                    ).lower()

                    if "text/html" in content_type:
                        raise RuntimeError(
                            f"Server returned HTML instead of {filename}"
                        )

                    with open(temporary, mode) as output:
                        for chunk in response.iter_content(
                            chunk_size=CHUNK_SIZE
                        ):
                            if chunk:
                                output.write(chunk)

                    expected = response.headers.get("Content-Length")

                    if expected and temporary.stat().st_size != (
                        existing_size + int(expected)
                    ):
                        raise RuntimeError(
                            f"Incomplete download: {filename}"
                        )

            if temporary.stat().st_size == 0:
                raise RuntimeError("Downloaded file is empty")

            temporary.replace(destination)

            return "downloaded", filename

        except Exception:
            if attempt == MAX_RETRIES:
                return "failed", f"{filename}: download failed"

            time.sleep(attempt * 2)

    return "failed", filename


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Reading NASA MOLA archive...")

    files = get_archive_files()

    if not files:
        raise RuntimeError("No MOLA topography files found")

    images = [
        f for f in files
        if f.lower().endswith(".img")
    ]

    print(f"Found {len(files)} files")
    print(f"Found {len(images)} topography image files")
    print(f"Using {MAX_WORKERS} parallel workers\n")

    results = {
        "downloaded": 0,
        "skipped": 0,
        "failed": []
    }

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_file, filename): filename
            for filename in files
        }

        with tqdm(total=len(futures), desc="MOLA files") as progress:
            for future in as_completed(futures):
                status, message = future.result()
                results[status] += 1 if status != "failed" else 0

                if status == "failed":
                    results["failed"].append(message)

                progress.update(1)
                progress.set_postfix(
                    downloaded=results["downloaded"],
                    skipped=results["skipped"],
                    failed=len(results["failed"])
                )

    print("\nDownload summary")
    print("----------------")
    print("Downloaded:", results["downloaded"])
    print("Already present:", results["skipped"])
    print("Failed:", len(results["failed"]))

    for failure in results["failed"]:
        print("ERROR:", failure)

    print("\nData directory:", OUTPUT_DIR.resolve())


if __name__ == "__main__":
    main()
