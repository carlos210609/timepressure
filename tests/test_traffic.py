from timepressure.models import PressureState, State
from timepressure.traffic import campaign_url, record_visit, start_campaign

def make_state():
    now = 1_000_000.0
    return State(1, now, PressureState(now, 10, 0, 0, "alive", now + 3600))

def test_campaign_url_adds_utm():
    url = campaign_url("https://example.com/page?x=1", "youtube", campaign="launch")
    assert "x=1" in url
    assert "utm_source=youtube" in url
    assert "utm_campaign=launch" in url

def test_campaign_records_verified_visits():
    state = make_state()
    start_campaign(state, "https://example.com", 10, "launch")
    record_visit(state, "analytics", 3, "event-1")
    assert state.traffic.verified_visits == 3
    assert state.traffic.status == "active"
    record_visit(state, "analytics", 7, "event-2")
    assert state.traffic.status == "completed"

def test_duplicate_reference_is_rejected():
    state = make_state()
    start_campaign(state, "https://example.com", 10, "launch")
    record_visit(state, "analytics", 1, "same")
    try:
        record_visit(state, "analytics", 1, "same")
        assert False
    except ValueError as exc:
        assert "Duplicate" in str(exc)
