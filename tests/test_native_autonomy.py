from timepressure.innovation import choose_focus,create_action_plan,memory_relevance,budget_guard,idle_detection,retry_backoff,action_fingerprint,safe_numeric,goal_progress,decision_confidence,circuit_breaker,resource_efficiency

def test_native_autonomy():
    assert choose_focus([{"goal":"A","value":100,"urgency":1,"effort":10}])["goal"]=="A"
    assert len(create_action_plan("ship"))==5
    assert memory_relevance("traffic engine",[{"title":"traffic","content":"engine"}])[0]["score"]==2
    assert budget_guard(90,100)["remainingCents"]==10
    assert idle_detection(0,1000,300)["idle"]
    assert retry_backoff(3)==8
    assert len(action_fingerprint(" Hello   World "))==16
    assert safe_numeric("9",low=0,high=5)==5
    assert goal_progress(3,5)["percent"]==60
    assert decision_confidence(5)>0
    assert circuit_breaker(3)["open"]
    assert resource_efficiency(10,60)["unitsPerMinute"]==10
