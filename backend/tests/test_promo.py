from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from owlin.api.app import app
from owlin.api.deps import get_current_user
from owlin.core.errors import ConflictError, InvalidRequestError, NotFoundError
from owlin.core.security import TokenUser
from owlin.modules.catalog.constants import MAX_PROMO_SLOTS, PROMO_DAYS
from owlin.modules.promo import review, service
from owlin.modules.promo.models import PromoClaim
from owlin.modules.promo.video_links import ParsedVideo, parse_video_link
from owlin.modules.subscriptions.models import SubscriptionGrant, UserSubscription
from tests.conftest import ServiceSession

NOW = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
ADMIN_ID = uuid4()


class TestParseVideoLink:
    @pytest.mark.parametrize(
        "url",
        [
            "https://www.youtube.com/watch?v=dKiSnET6eNs&t=5",
            "youtu.be/dKiSnET6eNs?si=abc",
            "https://m.youtube.com/shorts/dKiSnET6eNs",
            "https://www.youtube.com/live/dKiSnET6eNs",
            "  https://youtube.com/embed/dKiSnET6eNs  ",
        ],
    )
    def test_every_youtube_form_gives_the_same_key(self, url: str) -> None:
        assert parse_video_link(url, "youtube").key == "youtube:dKiSnET6eNs"

    def test_tiktok_key_comes_from_the_video_id(self) -> None:
        video = parse_video_link("https://www.tiktok.com/@user/video/7695863549985312021?lang=en", "tiktok")

        assert video.key == "tiktok:7695863549985312021"

    def test_other_links_ignore_tracking_noise(self) -> None:
        keys = {
            parse_video_link(url, "other").key
            for url in [
                "https://www.example.com/clip/",
                "https://example.com/clip?utm_source=x&fbclid=y",
                "example.com/clip#t=30",
            ]
        }

        assert keys == {"other:example.com/clip"}

    def test_other_links_keep_meaningful_query_parameters(self) -> None:
        assert parse_video_link("https://example.com/watch?id=42&utm_medium=z", "other").key == "other:example.com/watch?id=42"

    @pytest.mark.parametrize(
        "url, platform",
        [
            ("", "youtube"),
            ("not a url", "youtube"),
            ("localhost", "other"),
            ("https://vm.tiktok.com/ZMabc/", "tiktok"),
            ("https://www.tiktok.com/@user", "tiktok"),
            ("https://youtu.be/dKiSnET6eNs", "tiktok"),
            ("https://tiktok.com/@u/video/1", "youtube"),
            ("https://youtube.com/watch?v=short", "youtube"),
            ("https://youtu.be/dKiSnET6eNs", "other"),
            ("https://www.tiktok.com/@u/video/1", "other"),
        ],
    )
    def test_invalid_links_are_rejected(self, url: str, platform: str) -> None:
        with pytest.raises(InvalidRequestError):
            parse_video_link(url, platform)


YOUTUBE_URL = "https://youtu.be/dKiSnET6eNs"


class TestCheckAndCreate:
    @pytest.mark.asyncio
    async def test_a_new_video_with_a_free_slot_is_accepted(self) -> None:
        session = ServiceSession(scalar_values=[None, 3])

        video = await service.check_claim(session, uuid4(), "youtube", YOUTUBE_URL, "spoofer", NOW)

        assert video.key == "youtube:dKiSnET6eNs"

    @pytest.mark.asyncio
    async def test_a_video_that_is_already_open_or_approved_is_refused(self) -> None:
        session = ServiceSession(scalar_values=[uuid4(), 0])

        with pytest.raises(ConflictError, match="already used"):
            await service.check_claim(session, uuid4(), "youtube", YOUTUBE_URL, "spoofer", NOW)

    @pytest.mark.asyncio
    async def test_a_full_set_of_slots_blocks_new_claims(self) -> None:
        session = ServiceSession(scalar_values=[None, MAX_PROMO_SLOTS])

        with pytest.raises(ConflictError, match="slots"):
            await service.check_claim(session, uuid4(), "youtube", YOUTUBE_URL, "spoofer", NOW)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("platform, reward", [("vimeo", "spoofer"), ("youtube", "bundle"), ("youtube", "ets2")])
    async def test_unknown_platform_or_reward(self, platform: str, reward: str) -> None:
        with pytest.raises(InvalidRequestError):
            await service.check_claim(ServiceSession(), uuid4(), platform, YOUTUBE_URL, reward, NOW)

    @pytest.mark.asyncio
    async def test_creating_a_claim_stores_it_under_review_with_the_normalized_key(self) -> None:
        user_id = uuid4()
        session = ServiceSession(scalar_values=[None, 0])

        claim = await service.create_claim(
            session, user_id, "youtube", f"  {YOUTUBE_URL}?si=track  ", "dlc-unlock", now=NOW
        )

        assert (claim.status, claim.video_key, claim.reward_product) == ("review", "youtube:dKiSnET6eNs", "dlc-unlock")
        assert claim.user_id == user_id
        assert claim.url == f"{YOUTUBE_URL}?si=track"
        assert session.committed is True

    @pytest.mark.asyncio
    async def test_losing_a_race_for_the_same_video_is_a_conflict(self) -> None:
        session = ServiceSession(scalar_values=[None, 0])
        session.flush_error = IntegrityError("insert", {}, Exception("duplicate key"))

        with pytest.raises(ConflictError, match="already used"):
            await service.create_claim(session, uuid4(), "youtube", YOUTUBE_URL, "spoofer", now=NOW)

        assert session.rolled_back is True
        assert session.committed is False


def make_claim(**overrides: object) -> PromoClaim:
    values = dict(
        id=uuid4(), user_id=uuid4(), platform="youtube", video_key="youtube:x", url="https://youtu.be/x",
        reward_product="spoofer", status="review", created_at=NOW,
    )  # fmt: skip
    return PromoClaim(**{**values, **overrides})


def session_for(claim: PromoClaim, **subscription: object) -> ServiceSession:
    defaults = dict(
        spoofer_access=False, spoofer_expires_at=None, dlc_access=False, dlc_expires_at=None,
        ets2_access=False, ets2_expires_at=None, ets2mp_access=False, ets2mp_expires_at=None,
    )  # fmt: skip
    return ServiceSession({PromoClaim: claim, UserSubscription: UserSubscription(user_id=claim.user_id, **{**defaults, **subscription})})


class TestApproveClaim:
    @pytest.mark.asyncio
    async def test_grants_the_promo_days_and_keeps_the_slot_until_they_run_out(self) -> None:
        claim = make_claim()
        session = session_for(claim)

        result = await review.approve_claim(session, claim.id, ADMIN_ID, views=1500, now=NOW)

        assert (result.status, result.views) == ("approved", 1500)
        assert result.expires_at == NOW + timedelta(days=PROMO_DAYS)
        assert (result.reviewed_by, result.reviewed_at) == (ADMIN_ID, NOW)
        assert session.objects[UserSubscription].spoofer_expires_at == NOW + timedelta(days=PROMO_DAYS)
        [grant] = session.added_of(SubscriptionGrant)
        assert (grant.source, grant.promo_claim_id, grant.days) == ("promo", claim.id, PROMO_DAYS)
        assert session.committed is True

    @pytest.mark.asyncio
    async def test_free_days_stack_after_a_running_subscription(self) -> None:
        claim = make_claim(reward_product="dlc-unlock")
        running_until = NOW + timedelta(days=10)
        session = session_for(claim, dlc_access=True, dlc_expires_at=running_until)

        result = await review.approve_claim(session, claim.id, ADMIN_ID, views=2000, now=NOW)

        assert result.expires_at == running_until + timedelta(days=PROMO_DAYS)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("platform, views", [("youtube", 999), ("youtube", None), ("tiktok", 4999)])
    async def test_not_enough_views_is_refused(self, platform: str, views: int | None) -> None:
        claim = make_claim(platform=platform)
        session = session_for(claim)

        with pytest.raises(InvalidRequestError, match="views"):
            await review.approve_claim(session, claim.id, ADMIN_ID, views=views, now=NOW)

        assert claim.status == "review"
        assert session.added == []

    @pytest.mark.asyncio
    async def test_the_minimum_is_inclusive_and_other_platforms_need_no_number(self) -> None:
        for platform, views in [("youtube", 1000), ("tiktok", 5000), ("other", None)]:
            claim = make_claim(platform=platform)
            result = await review.approve_claim(session_for(claim), claim.id, ADMIN_ID, views=views, now=NOW)
            assert result.status == "approved"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", ["approved", "rejected"])
    async def test_a_decided_claim_cannot_be_approved_again(self, status: str) -> None:
        claim = make_claim(status=status)

        with pytest.raises(ConflictError):
            await review.approve_claim(session_for(claim), claim.id, ADMIN_ID, views=5000, now=NOW)

    @pytest.mark.asyncio
    async def test_unknown_claim(self) -> None:
        with pytest.raises(NotFoundError):
            await review.approve_claim(ServiceSession(), uuid4(), ADMIN_ID, views=5000, now=NOW)


class TestRejectClaim:
    @pytest.mark.asyncio
    async def test_records_the_reason_and_frees_the_video(self) -> None:
        claim = make_claim()
        session = session_for(claim)

        result = await review.reject_claim(session, claim.id, ADMIN_ID, " No mention of Owlin ", now=NOW)

        assert (result.status, result.reject_reason) == ("rejected", "No mention of Owlin")
        assert session.added == []
        assert session.committed is True

    @pytest.mark.asyncio
    async def test_an_approved_claim_cannot_be_rejected(self) -> None:
        claim = make_claim(status="approved")

        with pytest.raises(ConflictError):
            await review.reject_claim(session_for(claim), claim.id, ADMIN_ID, "late", now=NOW)


USER = TokenUser(id=uuid4(), username="Pedro", avatar_url=None)


class TestEndpoints:
    @pytest.fixture(autouse=True)
    def sign_in(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: USER

    @pytest.mark.asyncio
    async def test_promo_requires_a_token(self, client) -> None:
        app.dependency_overrides.pop(get_current_user)

        for method, path in [("post", "/api/promo/check"), ("post", "/api/promo/claims"), ("get", "/api/me/promo")]:
            assert (await getattr(client, method)(path)).status_code == 401

    @pytest.mark.asyncio
    async def test_check_reports_ok_or_the_reason(self, client, use_session, monkeypatch) -> None:
        use_session(ServiceSession())
        body = {"platform": "youtube", "url": YOUTUBE_URL, "reward_product": "spoofer"}

        async def accept(*_args):
            return ParsedVideo("youtube:x")

        monkeypatch.setattr(service, "check_claim", accept)
        assert (await client.post("/api/promo/check", json=body)).json() == {"status": "ok"}

        async def refuse(*_args):
            raise ConflictError("This video was already used for a promo reward. Submit a different one.")

        monkeypatch.setattr(service, "check_claim", refuse)
        response = await client.post("/api/promo/check", json=body)
        assert response.status_code == 409
        assert "already used" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_a_claim_is_created_with_status_201(self, client, use_session) -> None:
        use_session(ServiceSession(scalar_values=[None, 0]))

        response = await client.post(
            "/api/promo/claims", json={"platform": "youtube", "url": YOUTUBE_URL, "reward_product": "spoofer"}
        )

        assert response.status_code == 201
        body = response.json()
        assert (body["status"], body["platform"], body["reward_product"]) == ("review", "youtube", "spoofer")
        assert "video_key" not in body

    @pytest.mark.asyncio
    async def test_a_missing_url_is_a_validation_error(self, client, use_session) -> None:
        use_session(ServiceSession())

        response = await client.post("/api/promo/claims", json={"platform": "youtube", "url": "", "reward_product": "spoofer"})

        assert response.status_code == 422
