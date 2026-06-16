import requests
from datetime import datetime


def parse_year(data):
    """
    Parses the raw JSON response from the Aladhan API into a flat list
    of dicts, one per day, ready to be converted into a pandas DataFrame.

    Args:
        data (dict): The full JSON response from the API.

    Returns:
        list[dict]: A list of daily prayer time dicts.
    """
    days_parsed = []

    # data['data'] is a dict with month numbers as keys ('1' through '12')
    for month_days in data['data'].values():

        # Each month is a list of day objects
        for day in month_days:

            # Convert date from DD-MM-YYYY to YYYY-MM-DD
            raw_date = day['date']['gregorian']['date']
            date = datetime.strptime(raw_date, "%d-%m-%Y").strftime("%Y-%m-%d")

            # Build Hijri date string e.g. '12 Rajab 1447'
            hijri = day['date']['hijri']
            hijri_date = f"{hijri['day']} {hijri['month']['en']} {hijri['year']}"

            # Strip timezone suffix from times e.g. '06:25 (EST)' → '06:25'
            timings = day['timings']

            days_parsed.append({
                "Date":         date,
                "Weekday":      day['date']['gregorian']['weekday']['en'],
                "Hijri":        hijri_date,
                "Fajr_Start":   timings['Fajr'].split()[0],
                "Sunrise":      timings['Sunrise'].split()[0],
                "Dhuhr_Start":  timings['Dhuhr'].split()[0],
                "Asr_Start":    timings['Asr'].split()[0],
                "Maghrib_Start": timings['Maghrib'].split()[0],
                "Isha_Start":   timings['Isha'].split()[0],
            })

    return days_parsed


def get_yearly_start_time(year):
    """
    Fetches a full year of prayer start times from the Aladhan API
    and returns them as a parsed list of dicts.

    Args:
        year (int): The year to fetch, e.g. 2026.

    Returns:
        list[dict]: A list of daily prayer time dicts for the full year.
    """
    response = requests.get(
        f"https://api.aladhan.com/v1/calendar/{year}",
        params={
            "latitude": "43.6532",
            "longitude": "-79.3832",
            "method": 2,
            "school": 0,
            # "tune": config["tune"],           # minute offsets per prayer
            # "midnightMode": config["midnight_mode"],  # midnight calculation method
            # "shafaq": config["shafaq"],        # only used when method is 15
            # "timezonestring": config["timezone"],     # explicit timezone override
        },
        timeout=1
    )

    # Parse the raw JSON response into a clean list of dicts
    parsed_data = parse_year(response.json())
    return parsed_data


if __name__ == "__main__":
    # Run this file directly to test the API call and parser
    response = get_yearly_start_time(2026)
    print(response)