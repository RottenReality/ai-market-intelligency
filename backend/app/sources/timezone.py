from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def max_hour_difference(tz_a: str, tz_b: str, year: int) -> float:
    """Largest absolute UTC-offset difference in hours between two zones during a year.

    Sampled every day at 12:00 UTC, which catches the weeks where daylight-saving
    changes happen on different dates in each zone.
    """
    zone_a, zone_b = ZoneInfo(tz_a), ZoneInfo(tz_b)
    start = datetime.combine(date(year, 1, 1), time(12), tzinfo=UTC)
    days = (date(year + 1, 1, 1) - date(year, 1, 1)).days
    largest = 0.0
    for day in range(days):
        moment = start + timedelta(days=day)
        offset_a = moment.astimezone(zone_a).utcoffset() or timedelta()
        offset_b = moment.astimezone(zone_b).utcoffset() or timedelta()
        largest = max(largest, abs(offset_a - offset_b).total_seconds() / 3600)
    return largest
