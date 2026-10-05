"""Legitimate revenue strategy knowledge base for TimePressure.

This is a decision catalogue, not a promise of income. Strategies are scored at runtime
by expected value, time-to-value, confidence, cost and compliance risk.
"""

STRATEGIES = [
    # Digital products
    {"id":"micro_saas","category":"product","name":"Build a tiny SaaS","actions":"Find a narrow painful problem, build the smallest useful workflow, publish a landing page and charge for access.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"template_pack","category":"product","name":"Sell templates","actions":"Create reusable website, spreadsheet, design, prompt or developer templates and list them on an allowed marketplace.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"developer_tool","category":"product","name":"Sell a developer utility","actions":"Package a focused CLI, API wrapper, converter, checker or automation tool with paid tiers.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"api_service","category":"product","name":"Offer a paid API","actions":"Find a repetitive data transformation or enrichment task that can be exposed as a metered API.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"digital_download","category":"product","name":"Sell digital downloads","actions":"Create genuinely useful guides, assets, checklists, spreadsheets or code resources and sell them where automation is permitted.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"newsletter","category":"content","name":"Paid niche newsletter","actions":"Research a narrow audience, publish useful original analysis and offer a paid tier.","time":"long","value":"medium","cost":"low","automation":"medium"},
    # Services
    {"id":"website_audit","category":"service","name":"Website audit","actions":"Analyze public websites for UX, accessibility, performance and SEO issues and offer a fixed-price audit.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"seo_audit","category":"service","name":"SEO audit service","actions":"Find technical SEO problems on public sites and produce evidence-backed improvement reports.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"data_cleaning","category":"service","name":"Data cleanup","actions":"Offer spreadsheet/CSV cleaning, normalization, deduplication and transformation with client-provided data.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"automation_service","category":"service","name":"Business automation","actions":"Identify repetitive business workflows and offer scripts or integrations that save measurable time.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"research_service","category":"service","name":"Research briefs","actions":"Produce concise, sourced research reports for legitimate business questions.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"data_extraction","category":"service","name":"Public-data extraction","actions":"Collect and normalize permitted public information while respecting robots, terms and rate limits.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"translation","category":"service","name":"Translation/localization","actions":"Translate or localize client-provided material while preserving meaning and formatting.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"copy_editing","category":"service","name":"Copy editing","actions":"Improve client-provided copy for clarity, grammar, structure and conversion without deceptive claims.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"code_review","category":"service","name":"Code review","actions":"Review client-provided code for bugs, maintainability, security and performance issues.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"bug_fixing","category":"service","name":"Small bug fixes","actions":"Accept narrowly scoped programming tasks with clear acceptance criteria and deliver patches.","time":"short","value":"medium","cost":"low","automation":"high"},
    # Creator/content
    {"id":"content_repuposing","category":"content","name":"Content repurposing","actions":"Turn client-owned long-form material into shorts, posts, summaries and captions with permission.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"video_editing","category":"content","name":"Short-form editing","actions":"Edit client-provided footage into concise vertical videos with captions and pacing.","time":"medium","value":"medium","cost":"low","automation":"medium"},
    {"id":"thumbnail_design","category":"content","name":"Thumbnail design","actions":"Create thumbnails from client assets and a clear brief.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"social_content_pack","category":"content","name":"Social content pack","actions":"Create a batch of original posts from a client's approved topics and brand voice.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"ugc_script","category":"content","name":"UGC scripts","actions":"Write original short-form scripts for brands or creators using their approved claims and products.","time":"short","value":"medium","cost":"low","automation":"high"},
    # Lead generation / sales
    {"id":"lead_research","category":"sales","name":"Qualified lead research","actions":"Research public business information and build permission-aware prospect lists for a client.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"sales_intelligence","category":"sales","name":"Sales intelligence brief","actions":"Research a prospect company and produce a concise account brief with public evidence.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"proposal_drafting","category":"sales","name":"Proposal drafting","actions":"Turn a qualified lead's requirements into a tailored proposal for human approval.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"market_research","category":"sales","name":"Market research","actions":"Compare competitors, pricing and positioning using public sources and deliver a structured report.","time":"medium","value":"high","cost":"low","automation":"high"},
    # Affiliate / referrals
    {"id":"affiliate_content","category":"affiliate","name":"Affiliate content","actions":"Create honest comparison or tutorial content around products with legitimate affiliate programs and disclose the relationship.","time":"medium","value":"medium","cost":"low","automation":"high"},
    {"id":"referral_program","category":"affiliate","name":"Referral programs","actions":"Find programs that explicitly allow referrals and earn commissions from genuine users.","time":"short","value":"medium","cost":"low","automation":"medium"},
    # B2B recurring
    {"id":"monitoring_service","category":"recurring","name":"Website monitoring","actions":"Offer uptime, change, price or SEO monitoring where the monitored site permits automated checks.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"reporting_service","category":"recurring","name":"Automated reporting","actions":"Turn client data into scheduled dashboards or reports with explicit authorization.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"alerting_service","category":"recurring","name":"Business alerts","actions":"Create useful threshold alerts for approved data sources and charge a recurring fee.","time":"medium","value":"high","cost":"low","automation":"high"},
    # Open work / marketplaces
    {"id":"paid_marketplace_tasks","category":"marketplace","name":"Paid task marketplaces","actions":"Find legitimate marketplaces that permit automated agents, evaluate task economics and complete qualifying work.","time":"short","value":"medium","cost":"low","automation":"medium"},
    {"id":"bug_bounty","category":"security","name":"Authorized bug bounty","actions":"Work only within explicit program scope and report security issues responsibly.","time":"long","value":"high","cost":"low","automation":"medium"},
    {"id":"open_source_bounty","category":"development","name":"Open-source bounties","actions":"Find permitted coding bounties and submit quality patches that satisfy acceptance criteria.","time":"medium","value":"high","cost":"low","automation":"high"},
    # Infrastructure
    {"id":"compute_service","category":"infrastructure","name":"Small compute service","actions":"Offer a narrow, lawful compute or transformation endpoint where operating costs are lower than the price.","time":"long","value":"high","cost":"medium","automation":"high"},
    {"id":"proxy_service","category":"infrastructure","name":"Compliant network service","actions":"Only offer network infrastructure with explicit provider/customer permission and applicable legal compliance.","time":"long","value":"high","cost":"medium","automation":"medium"},
    # Education
    {"id":"mini_course","category":"education","name":"Mini-course","actions":"Package original expertise into a focused course solving one concrete problem.","time":"medium","value":"medium","cost":"low","automation":"high"},
    {"id":"study_material","category":"education","name":"Study materials","actions":"Create original study guides, practice sets and explanations without misrepresenting authorship.","time":"short","value":"medium","cost":"low","automation":"high"},
    # Data / intelligence
    {"id":"price_monitor","category":"data","name":"Price monitoring","actions":"Monitor permitted public prices and sell useful alerts or reports without abusing websites.","time":"medium","value":"medium","cost":"low","automation":"high"},
    {"id":"trend_report","category":"data","name":"Trend reports","actions":"Aggregate public signals into original niche trend reports with source attribution.","time":"short","value":"medium","cost":"low","automation":"high"},
    # Productized AI
    {"id":"ai_workflow","category":"ai","name":"AI workflow product","actions":"Combine model calls with deterministic software to solve a specific business workflow and charge for the outcome.","time":"medium","value":"high","cost":"medium","automation":"high"},
    {"id":"document_processing","category":"ai","name":"Document processing","actions":"Offer authorized extraction, classification, summarization or transformation of customer documents.","time":"medium","value":"high","cost":"medium","automation":"high"},
    {"id":"support_assistant","category":"ai","name":"Support assistant","actions":"Build a customer-approved support workflow that drafts or handles routine requests under clear escalation rules.","time":"medium","value":"high","cost":"medium","automation":"high"},
    # General
    {"id":"custom_integration","category":"development","name":"Custom integration","actions":"Connect two approved services through APIs/webhooks and charge for implementation or recurring maintenance.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"migration_service","category":"development","name":"Data migration","actions":"Migrate customer-owned data between compatible systems with backups, validation and explicit authorization.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"performance_optimization","category":"development","name":"Performance optimization","actions":"Measure and improve an authorized app's performance, then document measurable gains.","time":"medium","value":"high","cost":"low","automation":"high"},
    {"id":"documentation_service","category":"development","name":"Technical documentation","actions":"Turn existing code and product knowledge into accurate developer documentation.","time":"short","value":"medium","cost":"low","automation":"high"},
    {"id":"qa_testing","category":"development","name":"QA testing","actions":"Run authorized test plans, reproduce bugs and produce evidence-rich reports.","time":"short","value":"medium","cost":"low","automation":"high"},
]

CATEGORY_PRIORITY = {
    "service": 1.2, "development": 1.25, "recurring": 1.25,
    "product": 1.1, "ai": 1.15, "marketplace": 1.0,
    "data": 1.0, "sales": 0.95, "content": 0.9, "education": 0.85,
    "affiliate": 0.7, "infrastructure": 0.8, "security": 0.8,
}

def rank_strategies(pressure, seconds_left, active_categories=None):
    active_categories = set(active_categories or ())
    results = []
    urgency = 1.0 + (pressure / 100.0)
    for item in STRATEGIES:
        time_score = {"short":1.4, "medium":1.0, "long":0.55}[item["time"]]
        value_score = {"medium":1.0, "high":1.5}[item["value"]]
        automation_score = {"medium":1.0, "high":1.25}[item["automation"]]
        category_score = CATEGORY_PRIORITY.get(item["category"], 1.0)
        diversity = 1.15 if item["category"] not in active_categories else 0.9
        deadline = 1.3 if seconds_left < 900 and item["time"] == "short" else 1.0
        score = time_score * value_score * automation_score * category_score * diversity * deadline * urgency
        results.append({**item, "score": round(score, 4)})
    return sorted(results, key=lambda x: x["score"], reverse=True)

def top_strategies(pressure, seconds_left, limit=8, active_categories=None):
    return rank_strategies(pressure, seconds_left, active_categories)[:limit]
