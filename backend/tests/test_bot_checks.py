from types import SimpleNamespace

import pytest

from owlin.bot import checks

OWNER_ID = 1


def make_member(*, member_id=100, bot=False, position=1, administrator=False, kick_members=False):
    return SimpleNamespace(
        id=member_id,
        bot=bot,
        top_role=SimpleNamespace(position=position),
        guild_permissions=SimpleNamespace(administrator=administrator, kick_members=kick_members),
    )


GUILD = SimpleNamespace(owner_id=OWNER_ID)


class TestIsExempt:
    def test_an_ordinary_member_is_not_exempt(self) -> None:
        assert not checks.is_exempt(make_member(), GUILD)

    @pytest.mark.parametrize(
        "member",
        [
            make_member(bot=True),
            make_member(member_id=OWNER_ID),
            make_member(administrator=True),
            make_member(kick_members=True),
        ],
        ids=["bot", "owner", "administrator", "moderator"],
    )
    def test_bots_the_owner_administrators_and_moderators_are_exempt(self, member) -> None:
        assert checks.is_exempt(member, GUILD)


class TestCanActOn:
    def test_a_lower_role_can_be_moderated(self) -> None:
        assert checks.can_act_on(make_member(position=5), make_member(position=2))

    @pytest.mark.parametrize("target_position", [5, 7])
    def test_an_equal_or_higher_role_cannot(self, target_position: int) -> None:
        assert not checks.can_act_on(make_member(position=5), make_member(position=target_position))
