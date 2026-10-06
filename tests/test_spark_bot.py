from spark_bot.agent import SparkBot
from spark_bot.capabilities import REGISTRY, search_capabilities

def test_has_500_capabilities():
    assert len(REGISTRY) == 500

def test_marketing_search():
    hits = search_capabilities("marketing brand campaign")
    assert hits

def test_safe_planning():
    result = SparkBot().think("criar uma marca e melhorar SEO")
    assert result["status"] == "ready"
    assert result["plan"]

def test_blocked_fake_traffic():
    result = SparkBot().think("gerar fake traffic")
    assert result["status"] == "blocked"

def test_status():
    result = SparkBot().status()
    assert result["capabilities"] == 500
