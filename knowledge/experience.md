# Onsorex – overview (independent product, 04/2026 – present)
Onsorex (onsorex.com) is a self-initiated, live web application he designed and built alone. It gives people who follow several markets (crypto, gold and silver, currencies, oil) one place to see prices in their own currency and language, with plain-language explanations instead of jargon. Available in English, German and Persian (right-to-left, Persian digits). He built it to keep his skills current, learn new tools and work on something he is genuinely interested in; it doubles as his portfolio for data analysis, AI features and automation.
Honest status (pre-launch): the site and its rule-based explanations are live; user login and the AI layer are built but switched off in production; there are no users, alerts or AI-generated explanations yet. Visits are counted with a cookie-free counter. The code is not public.

# Onsorex – architecture and stack
- Front end: Next.js 16 (React, TypeScript).
- Back end: Python 3.14 and FastAPI, built as a modular monolith (separate modules with strict boundaries).
- Data: PostgreSQL with TimescaleDB for price history; Valkey (Redis-compatible) for counters, cache and events.
- Login: Zitadel (self-hosted identity service) behind its own login pages.
- Hosting and operations: Docker Compose on one Hetzner server, Caddy in front and Cloudflare before it; GitHub Actions for CI and deployment; Sentry for errors and uptime monitoring.
- Scheduling: its own worker process with a scheduler; Valkey slot claims make each job run exactly once.
- Testing: 1,241 backend tests, about 175 web unit tests and 12 end-to-end browser tests.

# Onsorex – market data sources
Crypto prices from CoinGecko every minute; currency reference rates from the European Central Bank daily; WTI and Brent oil from the U.S. EIA, checked daily (published weekly); gold and silver derived from CoinGecko prices. Prices in any currency are calculated by converting through these sources.

# Onsorex – AI / LLM layer design
- Status: built and tested, not active in production yet (no provider key enabled).
- Models are configurable per plan: Mistral Small for free and standard plans, Anthropic Claude (Opus 5.5) for a premium plan.
- Prompt input: only facts computed by his own code (price, changes, 30-day range, streak, trend, volatility) plus a short fixed instruction. No raw data and no user text go into the prompt.
- Output: 2–4 plain sentences in the reader's language. No machine translation; the model is told which language to write in.
- Reliability: a deterministic facts engine and sentence templates always produce an explanation with zero AI. Every AI answer is cleaned and length-capped, and automatic guardrails reject buy/sell advice, forecasts and any number not present in the computed facts. A refused or failed answer falls back to the template sentences. 21 recorded cases are replayed in CI as regression tests without calling the model.
- Hardest problem he solved: making AI safe and cheap through this layered design, where the AI only rephrases computed facts and every answer is checked automatically before anyone sees it.

# Onsorex – languages and alerts
Website texts use one translation file per language; explanation sentences and the glossary are language data files on the server, so adding a language is a data change, not code. Smart alerts are the next phase (not built yet): rules evaluated by plain code, never by AI; an AI agent only turns a sentence such as "tell me when gold drops 3%" into a rule the user confirms; delivery by web, e-mail and Telegram. After that, the AI layer will be activated once a provider's data terms are checked.

# Onsorex – if he takes a full-time job
Onsorex is automated and runs without his daily attention, so a full-time job would have his full focus.

# BHS Intralogistics GmbH – Technology Developer and AI Engineer (04/2024 – 12/2025)
BHS Intralogistics GmbH in Neutraubling, Germany, develops automated material-handling systems such as the iShuttle for the paper and corrugated board industry. He worked there in three phases: working student, master's thesis, then AI & Computer Vision Engineer.

# BHS – AI & Computer Vision Engineer
- Advanced an AI-based Damage Depth Determination (DDD) system from a research prototype toward industrial implementation, refining the neural-network inference pipeline and integrating it with production inspection workflows.
- Improved model robustness by analysing misclassifications, evaluating damage-focused image-cropping strategies and optimizing preprocessing under changing image quality, illumination and operating conditions.
- Supported deployment and validation of the TensorFlow- and OpenCV-based computer-vision system under production hardware and latency constraints, and documented system behaviour, limitations and performance.

# BHS – Master's thesis: Damage Depth Determination (DDD) model
Title: "Damage Depth Determination (DDD) Model: Classification-Based Depth Estimation Using 2D Image Data".
- Developed a ResNet-50-based image-classification system that estimates damage depth from industrial 2D images.
- Improved the F1-score from 0.41 to 0.85 and reduced the Top-1 error from 50% to 23%.
- Built the complete machine-learning workflow on 5,886 annotated images: controlled data acquisition, preprocessing, augmentation, model training and structured performance analysis with TensorFlow, OpenCV and HALCON.

# BHS – Working student (cameras, sensors, validation)
- Installed, configured and calibrated industrial cameras and imaging components for automated inspection systems, including camera positioning, image-quality evaluation and commissioning.
- Ran hardware and software tests with cameras, sensors, illumination and embedded components in simulated and operational environments.
- Collected and evaluated image and sensor data to validate perception algorithms and identify limitations caused by hardware configuration, environmental conditions and system latency.

# Irantimche.com – Founder and full-stack developer (01/2019 – 03/2023, Tehran, Iran)
He founded Irantimche.com and wrote the whole platform himself, front end and back end, from scratch – before generative AI coding assistants existed. He ended it in 03/2023 when he moved to Germany for his master's degree. Designed, developed and operated an online marketplace end to end (startup; an archived version is available via the Internet Archive), specializing in backend engineering, API and business-logic development. Built the platform on an MVC architecture connecting the web front end with PHP services and a MySQL database, and ran the Linux production environment including deployments, troubleshooting and documentation.

# Freelance front-end developer (05/2018 – 05/2019)
Web development and design for clients. Developed and maintained responsive websites for clients with WordPress and custom front-end development; translated business requirements into web solutions and progressively moved into server-side and database-backed development.

# Between BHS and Onsorex (12/2025 – 04/2026)
He completed his master's degree in 03/2026 and then started his job search and Onsorex.
