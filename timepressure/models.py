from dataclasses import dataclass, field
from typing import Any, Literal


AgentStatus = Literal["alive", "warning", "critical", "dead"]


@dataclass
class PressureState:
    cycle_started_at: float
    target_cents: int
    cycle_revenue_cents: int
    pressure: float
    status: AgentStatus
    deadline: float
    last_revenue_at: float | None = None


@dataclass
class RevenueEvent:
    id: str
    cents: int
    source: str
    reference: str
    timestamp: float


@dataclass
class PayoutEvent:
    id: str
    revenue_references: list[str]
    revenue_cents: int
    ltc_amount: float
    ltc_usd_rate: float
    address: str
    txid: str
    timestamp: float


@dataclass
class MemoryEvent:
    id: str
    type: str
    text: str
    timestamp: float
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserEvent:
    id: str
    action: str
    url: str
    title: str
    timestamp: float


@dataclass
class State:
    version: int
    created_at: float
    pressure: PressureState
    revenue: list[RevenueEvent] = field(default_factory=list)
    payouts: list[PayoutEvent] = field(default_factory=list)
    memory: list[MemoryEvent] = field(default_factory=list)
    browser_history: list[BrowserEvent] = field(default_factory=list)
    working_goal: str = "Generate legitimate value and record verified revenue."
    working_plan: list[str] = field(default_factory=list)
    last_thought: str | None = None

    def to_dict(self):
        return {
            "version": self.version,
            "createdAt": self.created_at,
            "pressure": {
                "cycleStartedAt": self.pressure.cycle_started_at,
                "targetCents": self.pressure.target_cents,
                "cycleRevenueCents": self.pressure.cycle_revenue_cents,
                "pressure": self.pressure.pressure,
                "status": self.pressure.status,
                "deadline": self.pressure.deadline,
                "lastRevenueAt": self.pressure.last_revenue_at,
            },
            "revenue": [vars(x) for x in self.revenue],
            "payouts": [vars(x) for x in self.payouts],
            "memory": [vars(x) for x in self.memory],
            "browserHistory": [vars(x) for x in self.browser_history[-200:]],
            "working": {
                "goal": self.working_goal,
                "plan": self.working_plan,
                "lastThought": self.last_thought,
            },
        }

    @classmethod
    def from_dict(cls, d):
        p = d["pressure"]
        pressure = PressureState(
            float(p["cycleStartedAt"]),
            int(p["targetCents"]),
            int(p["cycleRevenueCents"]),
            float(p["pressure"]),
            p["status"],
            float(p["deadline"]),
            p.get("lastRevenueAt"),
        )
        return cls(
            int(d.get("version", 1)),
            float(d.get("createdAt", pressure.cycle_started_at)),
            pressure,
            [
                RevenueEvent(
                    x["id"],
                    int(x["cents"]),
                    x["source"],
                    x["reference"],
                    float(x["timestamp"]),
                )
                for x in d.get("revenue", [])
            ],
            [
                PayoutEvent(
                    x["id"],
                    list(x.get("revenue_references", x.get("revenueReferences", []))),
                    int(x.get("revenue_cents", x.get("revenueCents", 0))),
                    float(x.get("ltc_amount", x.get("ltcAmount", 0))),
                    float(x.get("ltc_usd_rate", x.get("ltcUsdRate", 0))),
                    x["address"],
                    x["txid"],
                    float(x["timestamp"]),
                )
                for x in d.get("payouts", [])
            ],
            [
                MemoryEvent(
                    x["id"],
                    x["type"],
                    x["text"],
                    float(x["timestamp"]),
                    x.get("metadata", {}),
                )
                for x in d.get("memory", [])
            ],
            [
                BrowserEvent(
                    x["id"],
                    x["action"],
                    x["url"],
                    x.get("title", ""),
                    float(x["timestamp"]),
                )
                for x in d.get("browserHistory", [])
            ],
            d.get("working", {}).get(
                "goal", "Generate legitimate value and record verified revenue."
            ),
            d.get("working", {}).get("plan", []),
            d.get("working", {}).get("lastThought"),
        )


@dataclass
class Config:
    target_cents: int
    cycle_ms: int
    tick_ms: int
    data_dir: str
    model: str
    api_key: str | None
    base_url: str
    ai_provider: str
    nvidia_api_key: str | None
    nvidia_model: str
    nvidia_base_url: str
    allow_network: bool
    browser_enabled: bool
    browser_headless: bool
    browser_allowed_domains: list[str]
    ltc_rpc_url: str
    ltc_rpc_user: str | None
    ltc_rpc_password: str | None
    ltc_payout_address: str | None
    ltc_min_payout: float
    ltc_auto_payout: bool
    ltc_usd_rate: float | None
    shell_enabled: bool
    temp_email_enabled: bool
    temp_email_target_domains: list[str]
    temp_email_provider_domains: list[str]
    temp_email_providers: list[dict[str, str]]
