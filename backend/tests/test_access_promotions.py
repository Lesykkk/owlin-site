from datetime import UTC, datetime, time

import pytest

from owlin.modules.access_promotions import service
from owlin.modules.access_promotions.service import PromotionRow, active_promotions, window_end
from tests.conftest import FakeSession

NOW = datetime(2026, 10, 30, 12, 0, tzinfo=UTC)  # a Friday


def make_promotion(**values: object) -> PromotionRow:
    fields = {
        "name": "Free DLC",
        "promotion_type": "date_range",
        "timezone": "UTC",
        "spoofer_access": False,
        "dlc_access": True,
        "starts_at": datetime(2026, 10, 1, tzinfo=UTC),
        "ends_at": datetime(2026, 11, 1, tzinfo=UTC),
        "start_day": None,
        "end_day": None,
        "start_time": None,
        "end_time": None,
    }
    return PromotionRow(**{**fields, **values})


def make_weekly(start: tuple[int, time], end: tuple[int, time], **values: object) -> PromotionRow:
    """A weekly window from (day, time) to (day, time); days count from Sunday = 0."""
    fields = {
        "promotion_type": "weekly",
        "starts_at": None,
        "ends_at": None,
        "start_day": start[0],
        "start_time": start[1],
        "end_day": end[0],
        "end_time": end[1],
    }
    return make_promotion(**{**fields, **values})


class TestDateRange:
    def test_runs_between_start_and_end(self) -> None:
        assert window_end(make_promotion(), NOW) == datetime(2026, 11, 1, tzinfo=UTC)

    def test_has_not_started_yet(self) -> None:
        assert window_end(make_promotion(starts_at=datetime(2026, 11, 2, tzinfo=UTC), ends_at=datetime(2026, 12, 1, tzinfo=UTC)), NOW) is None

    def test_is_over_at_the_end_moment(self) -> None:
        assert window_end(make_promotion(ends_at=NOW), NOW) is None

    def test_an_open_end_never_runs(self) -> None:
        # The database function compares with NULL, which is never true.
        assert window_end(make_promotion(ends_at=None), NOW) is None


class TestWeekly:
    def test_inside_a_window_within_the_week(self) -> None:
        promotion = make_weekly((5, time(0, 0)), (6, time(0, 0)))  # Friday 00:00 to Saturday 00:00

        assert window_end(promotion, NOW) == datetime(2026, 10, 31, 0, 0, tzinfo=UTC)

    def test_outside_the_window(self) -> None:
        promotion = make_weekly((1, time(0, 0)), (3, time(0, 0)))  # Monday to Wednesday

        assert window_end(promotion, NOW) is None

    def test_a_window_that_wraps_around_the_end_of_the_week(self) -> None:
        promotion = make_weekly((5, time(18, 0)), (1, time(6, 0)))  # Friday 18:00 to Monday 06:00

        assert window_end(promotion, datetime(2026, 10, 31, 12, 0, tzinfo=UTC)) == datetime(2026, 11, 2, 6, 0, tzinfo=UTC)
        assert window_end(promotion, NOW) is None  # Friday 12:00 is before it opens

    def test_the_week_starts_on_sunday(self) -> None:
        promotion = make_weekly((0, time(0, 0)), (1, time(0, 0)))  # Sunday only

        assert window_end(promotion, datetime(2026, 11, 1, 12, 0, tzinfo=UTC)) == datetime(2026, 11, 2, 0, 0, tzinfo=UTC)
        assert window_end(promotion, NOW) is None

    def test_follows_the_time_zone_of_the_promotion(self) -> None:
        # 12:00 UTC is 14:00 in Kyiv (UTC+2 in late October); the window ends Friday 15:00 Kyiv = 13:00 UTC.
        promotion = make_weekly((5, time(0, 0)), (5, time(15, 0)), timezone="Europe/Kyiv")

        assert window_end(promotion, NOW) == datetime(2026, 10, 30, 13, 0, tzinfo=UTC)

    def test_equal_start_and_end_never_runs(self) -> None:
        assert window_end(make_weekly((5, time(0, 0)), (5, time(0, 0))), NOW) is None

    def test_missing_fields_never_run(self) -> None:
        assert window_end(make_weekly((5, time(0, 0)), (6, time(0, 0)), start_day=None), NOW) is None


class TestActivePromotions:
    def test_lists_only_the_sold_modules(self) -> None:
        promotion = make_promotion(spoofer_access=True, dlc_access=True)

        result = active_promotions([promotion], NOW)

        assert [(item.name, item.modules) for item in result] == [("Free DLC", ["spoofer", "dlc-unlock"])]

    def test_skips_a_promotion_that_opens_no_sold_module(self) -> None:
        # ETS2 flags are not on PromotionRow at all: they are never reported.
        assert active_promotions([make_promotion(dlc_access=False)], NOW) == []

    def test_skips_promotions_that_are_not_running(self) -> None:
        assert active_promotions([make_promotion(ends_at=datetime(2026, 10, 1, tzinfo=UTC), starts_at=datetime(2026, 9, 1, tzinfo=UTC))], NOW) == []

    def test_the_one_ending_first_comes_first(self) -> None:
        later = make_promotion(name="Later", ends_at=datetime(2026, 12, 1, tzinfo=UTC))
        sooner = make_promotion(name="Sooner")

        assert [item.name for item in active_promotions([later, sooner], NOW)] == ["Sooner", "Later"]


@pytest.mark.asyncio
async def test_endpoint_is_public_and_cacheable(client, use_session, monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_rows(_session: object) -> list[PromotionRow]:
        return [make_promotion(ends_at=datetime(2099, 1, 1, tzinfo=UTC))]

    monkeypatch.setattr(service, "load_rows", fake_rows)
    use_session(FakeSession())

    response = await client.get("/api/promotions/active")

    assert response.status_code == 200
    assert response.json() == {"promotions": [{"name": "Free DLC", "modules": ["dlc-unlock"], "ends_at": "2099-01-01T00:00:00Z"}]}
    assert response.headers["cache-control"] == "public, max-age=30"
