from timepressure.models import PressureState, State
from timepressure.social import approve_post, queue_post, record_metrics, register_account


def make_state():
    now = 1_000_000.0
    return State(1, now, PressureState(now, 10, 0, 0, "alive", now + 3600))


def test_social_account_and_post_flow():
    state = make_state()
    account = register_account(state, "x", "@example", "x-account-1", connected=True)
    post = queue_post(state, account.id, "A useful post", "https://example.com", "launch")
    assert post.status == "draft"
    approve_post(state, post.id)
    assert post.status == "approved"
    record_metrics(state, post.id, clicks=12, visits=8)
    assert post.clicks == 12
    assert post.visits == 8


def test_social_rejects_unknown_platform():
    state = make_state()
    try:
        register_account(state, "unknown", "x", "1")
        assert False
    except ValueError as exc:
        assert "Unsupported platform" in str(exc)
