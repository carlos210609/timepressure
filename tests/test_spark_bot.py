from spark_bot.agent import SparkBot
from spark_bot.capabilities import REGISTRY, get_skill

def test_exact_registry_size():
    assert len(REGISTRY) == 1500
    assert len({s.id for s in REGISTRY.values()}) == 1500

def test_metadata():
    s = get_skill("018.06")
    assert s.inputs and s.outputs and s.verification_method
    assert s.version == "1.0.0"

def test_router():
    assert SparkBot().discover("instagram content strategy")

def test_policy_blocks_fake_traffic():
    assert SparkBot().think("gerar fake traffic")["status"] == "blocked"

def test_dry_run_execution():
    out = SparkBot().run_skill("001.01", "entender meu objetivo", mode="DRY_RUN")
    assert out["status"] == "verified"

def test_status():
    assert SparkBot().status()["skills"] == 1500
