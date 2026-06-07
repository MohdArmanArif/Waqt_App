import requests

# Base URL for the Aladhan API — all endpoints are built on top of this
ALADHAN_BASE_URL = "https://api.aladhan.com/v1"


def fetch_year(year, config):
    """
    Fetches prayer times for an entire year from the Aladhan API in one call.

    Args:
        year (int): The year to fetch, e.g. 2026
        config (dict): The synced mosque config containing location and
                       calculation settings. Expected keys:
                       latitude, longitude, timezone, method, school

    Returns:
        list[dict]: A list of daily prayer time dicts for the entire year.
                    Each dict contains the date and all prayer times.
                    Returns an empty list if the request fails.
    """

    # Yearly endpoint — returns all 12 months in one response
    url = f"{ALADHAN_BASE_URL}/calendar/{year}"

    params = {
        "latitude": config["latitude"],
        "longitude": config["longitude"],
        "method": config["method"],
        "school": config["school"],
        "tune": config["tune"],
        "midnightMode": config["midnight_mode"],
        "shafaq": config["shafaq"],
        "timezonestring": config["timezone"],
    }

    print(f"[aladhan] Fetching full year {year}...")

    try:
        response = requests.get(url, params=params, timeout=1)
        response.raise_for_status()
        data = response.json()

        # The yearly endpoint returns a dict of months, each containing
        # a list of days — we flatten it into one list of all days
        # data["data"] looks like: { "1": [...], "2": [...], ... "12": [...] }
        all_days = []
        for day_num in data["data"].values():
            all_days.extend(day_num)

        print(f"[aladhan] Got {len(all_days)} days for {year}")
        return all_days

    except requests.RequestException as e:
        print(f"[aladhan] Failed to fetch year {year}: {e}")
        return []