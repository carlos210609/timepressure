from timepressure.innovation import adaptive_pressure,campaign_health,content_variants,dedupe_reference,detect_revenue_anomaly,experiment_score,forecast_cycle_revenue,pressure_projection,risk_gate,score_opportunity,utm_link

def test_score_and_forecast():
    assert score_opportunity(10,20,.8).score>0
    assert forecast_cycle_revenue([100,200],3600,7200)["forecastCents"]==600

def test_pressure_and_health():
    assert adaptive_pressure(1.5,80,.2)>1.5
    assert campaign_health(80,100,50,100)["status"]=="ahead"
    assert pressure_projection(50,2,30)["projectedNextMinute"]>50

def test_safety_and_integrity():
    assert risk_gate("local:inspect",network=False)["allowed"]
    assert not risk_gate("publish",external_write=True)["allowed"]
    assert dedupe_reference(["a","a","b"])["duplicates"]==["a"]

def test_experiments_and_copy():
    assert experiment_score(10,12,100)["deltaPct"]==20
    assert len(content_variants("TimePressure","https://example.com"))==3
    assert "utm_source=x" in utm_link("https://example.com","x","launch")

def test_anomaly():
    assert detect_revenue_anomaly([100,100,100,100,1000])["anomaly"]
