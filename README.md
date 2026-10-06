# Spark Bot

Spark Bot is the evolution of TimePressure into a general-purpose AI agent with **500 explicit capabilities** for reasoning, research, everyday work, brand building, marketing, SEO, content, social strategy, analytics, automation, engineering, security, finance, sales, customer operations and creative work.

## Core idea

Spark Bot does not rely on one giant prompt and pretend that it has hundreds of skills. It has a searchable, testable capability registry with 500 callable handlers and a planner that selects the relevant capabilities for each objective.

## Run

python3 sparkbot.py status
python3 sparkbot.py skills
python3 sparkbot.py skills --category marketing
python3 sparkbot.py think "criar uma marca e montar um plano de lançamento"
python3 sparkbot.py think "aumentar o tráfego orgânico de um site"
python3 sparkbot.py policy
python3 sparkbot.py pressure 80

## Capabilities

20 domains x 25 capabilities = 500 capabilities.

The agent can reason about:
- general decisions and complex planning
- research and evidence
- normal day-to-day tasks
- writing and communication
- brand creation and positioning
- SEO and organic traffic
- content and social strategy
- marketing funnels and campaigns
- analytics and attribution
- workflow automation
- software engineering
- security and privacy
- finance and unit economics
- productivity
- customer success
- sales
- creative work
- operations

## Account and marketing guardrails

Spark Bot does **not** create fake/disposable accounts to bypass platform requirements. Disposable identities can be abused and can violate platform rules.

It can instead:
- create local test identities for development;
- prepare official signup flows;
- use OAuth/API integrations when explicitly authorized;
- operate accounts only when the service permits automation and the required authorization exists.

Marketing is focused on legitimate acquisition: SEO, useful content, authorized social publishing, opt-in communication, partnerships, directories, conversion optimization and measurable analytics.

It does not generate fake traffic, fake clicks, fake impressions, spam, deceptive engagement, CAPTCHA bypasses, credential theft or unauthorized posting.

## NVIDIA

The existing NVIDIA integration can remain the reasoning provider. Keep NVIDIA_API_KEY in the environment only; never commit API keys.

## Architecture

SparkBot -> planner -> 500 capability registry -> policy/authorization -> external tools -> verification -> memory

The current repository remains public at:
https://github.com/carlos210609/timepressure
