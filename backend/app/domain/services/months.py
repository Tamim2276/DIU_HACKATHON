"""Small calendar helpers shared by the rules."""
import calendar
from datetime import date


def month_of(day: date) -> tuple[int, int]:
    return day.year, day.month


def add_months(month: tuple[int, int], count: int) -> tuple[int, int]:
    """The month `count` months after `month` (or before, for a negative count)."""
    index = month[0] * 12 + (month[1] - 1) + count
    return index // 12, index % 12 + 1


def previous_months(day: date, count: int) -> list[tuple[int, int]]:
    """The `count` complete months before the month of `day`, oldest first."""
    return [add_months(month_of(day), -back) for back in range(count, 0, -1)]


def day_in_month(month: tuple[int, int], day: int) -> date:
    """The given day of the month, or the month's last day when the month is shorter."""
    return date(month[0], month[1], min(day, calendar.monthrange(*month)[1]))
