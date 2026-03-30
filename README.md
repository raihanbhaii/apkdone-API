# 🚀 APKDone API: The Ultimate Enterprise-Grade Asynchronous Scraper & Wrapper

<div align="center">

![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-05998b?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![ScraperAPI](https://img.shields.io/badge/Powered%20By-ScraperAPI-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-BSD--3--Clause-orange.svg?style=for-the-badge)

**Elevating APK Data Retrieval to Enterprise Standards.**
*An aggressively optimized, heavily rate-limited, and deeply structured RESTful gateway for extracting mobile application telemetry and binaries.*

</div>

---

## 📖 1. Comprehensive Project Vision & Architectural Philosophy

The modern web is a hostile environment for automated data extraction. Sites employ advanced fingerprinting, aggressive rate limits, JavaScript challenges, and dynamic DOM rendering to prevent programmatic access. The **APKDone API** was engineered from the ground up to abstract this hostility. It serves as an invisible, highly performant middleware layer between your frontend applications and the raw, unstructured HTML of the target source.

Instead of writing brittle web scraping scripts that break every time a CSS class changes, this API provides a fortified RESTful interface. By leveraging the asynchronous capabilities of modern Python, this system can handle heavy concurrent loads without blocking the main event loop. Whether you are building an automated Android system modification tool, a custom ROM repository, a generic application tracker, or an expansive mobile gaming database, this API ensures that your data pipelines remain uncorrupted and your frontend interfaces remain pristine.

This is not just a scraper. It is a highly fault-tolerant data ingestion pipeline designed for production environments.

> [!CAUTION]
> **Strict Educational Notice:** This software architecture is provided strictly as a proof-of-concept for educational research regarding asynchronous HTTP handling, proxy rotation, and DOM parsing. The maintainers of this repository assume zero liability for how this code is deployed. You are entirely responsible for ensuring your usage complies with the target domain's Terms of Service and local data regulations.

---

## ✨ 2. Deep Dive: Advanced Feature Suite & Technology Stack

To achieve true reliability, we had to carefully select every component of our technology stack. Here is an exhaustive breakdown of what powers this API under the hood:

* **⚡ Pure Asynchronous Non-Blocking I/O:** 
  Built entirely on `FastAPI` and the `HTTPX` client. Traditional scrapers using `requests` block the server thread while waiting for a network response. Our architecture yields the thread back to the event loop, allowing a single server instance to handle hundreds of concurrent proxy requests simultaneously.
* **🛡️ Stealth Proxy Routing via ScraperAPI:** 
  Directly scraping from a single IP address will result in a permanent ban within minutes. We have natively integrated ScraperAPI to route every single outgoing request through a massive pool of residential and datacenter proxies. This completely neutralizes IP-based rate limiting and automatically solves intermediate CAPTCHAs.
* **🚦 Intelligent Traffic Control (SlowAPI):** 
  To prevent malicious actors from draining your proxy credits, the API is shielded by `SlowAPI`. We enforce a strict but fair limit of 10 requests per minute per IP. This ensures high availability and prevents denial-of-service vectors.
* **🧹 Recursive DOM Parsing and Sanitization:** 
  HTML is inherently messy. We utilize `BeautifulSoup4` with the highly optimized `lxml` C-backend to traverse the DOM tree. The data is then scrubbed, validated, and serialized into strict JSON schemas. Your frontend will never have to parse a raw HTML string again.
* **🌍 Cross-Origin Resource Sharing (CORS):** 
  The application is pre-configured with a permissive CORS middleware, meaning it is instantly ready to be consumed by modern web frameworks like React, Vue, or Next.js, directly from the browser without throwing preflight errors.

---

## 🤖 3. The Claude AI Expansion Protocol (Supercharging Development)

This API is built to be a foundational layer, but the real magic happens when you rapidly scale its features. If you want to add complex, enterprise-level functionality without spending hours digging through documentation, **we highly recommend utilizing Claude AI as your co-pilot.**

Here is the exact workflow to exponentially speed up your feature additions:

1. **Copy the Architecture:** Highlight and copy the contents of `app.py`, `requirements.txt`, and this very `README.md`.
2. **Deploy to Claude AI:** Paste the entire stack into a new Claude AI prompt. Claude's massive context window is perfect for understanding the full scope of this FastAPI structure.
3. **Execute Expansion Prompts:** Use targeted prompts to have Claude write the code for you. Try asking Claude:
   * *"Hey Claude, based on this FastAPI structure, write a new async route that scrapes the 'Top Grossing' category and implement Redis disk caching so we don't burn through ScraperAPI credits."*
   * *"Claude, modify the BeautifulSoup parsing logic in the `/app` endpoint to also extract the underlying OBB file size and inject it into the JSON response."*
   * *"Claude, write a background task script that pings the `/trending` endpoint every 24 hours and sends a formatted Discord webhook with the top 5 games."*
4. **Merge & Push:** Take the heavily optimized, context-aware code Claude generates, drop it back into your local repository, and push the commit. You just did a week's worth of backend engineering in 10 minutes.

---

## 🚀 4. The Exhaustive Deployment & Installation Guide

Deploying this API requires precision. Whether you are spinning this up on a local Windows machine, an Ubuntu VPS, or a cloud platform like Render or Vercel, follow these steps exactly to ensure environmental consistency.

### Phase 1: Environment Initialization
You must use Python 3.11 or higher to take advantage of the latest `asyncio` optimizations.

~~~bash
# 1. Clone the repository into your local or remote workspace
git clone https://github.com/OfficialRageAI/apkdone-API.git
cd apkdone-API

# 2. Establish a heavily isolated virtual environment
# This prevents global package conflicts and ensures runtime stability.
python -m venv venv

# 3. Activate the environment
# For Linux/Ubuntu VPS environments:
source venv/bin/activate
# For Windows PowerShell environments:
.\venv\Scripts\Activate.ps1
~~~

### Phase 2: Dependency Injection

Do not attempt to install packages manually. The `requirements.txt` file contains the exact version hashes required for the system to remain stable.

~~~bash
# Upgrade pip to the latest version to avoid wheel building errors
python -m pip install --upgrade pip

# Inject the core dependencies
pip install -r requirements.txt
~~~

### Phase 3: Cryptographic & Environment Configuration

The API will absolutely refuse to run without a valid ScraperAPI key. You must create a `.env` file in the root directory.

~~~bash
# Create the .env file
touch .env

# Open the file and insert your credentials. Never commit this file to GitHub!
echo "SCRAPER_API_KEY=insert_your_actual_64_character_scraper_api_key_here" >> .env
~~~

### Phase 4: Server Ignition

Start the ASGI server using Uvicorn. The `--reload` flag should only be used in local development. For a production Ubuntu VPS, you should run this behind a reverse proxy like Nginx and manage the process with `systemd` or `pm2`.

~~~bash
# Local Development Run
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
~~~

---

## 🛣️ 5. Exhaustive API Endpoint Documentation

Every endpoint is designed to return HTTP 200 on success, and appropriate 4xx or 5xx codes on failure. All responses are encapsulated in a standard JSON wrapper.

### 5.1. System Health (`GET /`)
* **Purpose:** Acts as a heartbeat monitor for the server. Also provides a quick-reference map of all active routes.
* **Rate Limit:** None.

### 5.2. The Dashboard Feed (`GET /home`)
* **Purpose:** Scrapes the homepage to aggregate the "Editor's Choice", "Newly Updated", and "Most Popular" sections.
* **Rate Limit:** 10/minute.

### 5.3. Trending Analytics (`GET /trending`)
* **Purpose:** Extracts the top charting applications across the entire platform. Useful for building a "Top 10" UI component.
* **Rate Limit:** 10/minute.

### 5.4. Paginated Game Library (`GET /games`)
* **Purpose:** Iterates through the dedicated gaming catalog.
* **Parameters:** `page` (integer, optional, defaults to 1).

### 5.5. Taxonomy & Classification (`GET /categories`)
* **Purpose:** Generates a complete map of all application categories (e.g., Action, RPG, Productivity, Tools).

### 5.6. Category Deep Dive (`GET /category/{slug}`)
* **Purpose:** Fetches all applications within a specific genre.
* **Parameters:** `slug` (string, required in path), `page` (integer, optional).

### 5.7. Global Query Engine (`GET /search`)
* **Purpose:** Submits a URL-encoded query to the target's search engine and parses the result grid.
* **Parameters:** `q` (string, required).

### 5.8. Metadata & Extraction Payload (`GET /app`)
* **Purpose:** The core functionality of the API. Pass the URL of a specific application page, and this endpoint will bypass the ad-walls, parse the metadata, extract the version history, and fetch the direct CDN download links.
* **Parameters:** `url` (string, required).

---

## 🧪 6. Standardized JSON Response Schema

We strictly adhere to a predictable data schema. You will never have to guess the shape of the data. Here is what you get when you ping the `/app` endpoint:

~~~json
{
  "status": "success",
  "endpoint_latency_ms": 1402,
  "data": {
    "metadata": {
      "title": "Example Mobile Application",
      "version": "v4.1.2 (Vanilla System)",
      "developer_studio": "Example Studio Global",
      "category": "Tools & Optimization",
      "file_size": "128 MB",
      "last_updated": "2026-03-30",
      "google_play_rating": 4.8
    },
    "description_html": "<p>This is the official description scraped and sanitized.</p>",
    "media": {
      "icon": "https://cdn.example.com/icon.png",
      "screenshots": [
        "https://cdn.example.com/screen1.jpg",
        "https://cdn.example.com/screen2.jpg"
      ]
    },
    "download_artifacts": [
      {
        "architecture": "arm64-v8a",
        "type": "APK",
        "cdn_link": "https://apkdone.com/dl/node-1/secure-token"
      },
      {
        "architecture": "universal",
        "type": "OBB",
        "cdn_link": "https://apkdone.com/dl/node-2/secure-token"
      }
    ]
  }
}
~~~

---

## 🛑 7. Error Handling & Exception Management

If something goes wrong, the API fails gracefully with informative JSON payloads rather than crashing the server.

* **400 Bad Request:** You forgot to pass a required parameter (like the `url` for the `/app` route).
* **403 Forbidden:** Your ScraperAPI key is invalid, missing, or out of credits. Check your `.env` file immediately.
* **429 Too Many Requests:** You have hit the SlowAPI rate limit. Back off and try again in 60 seconds to avoid IP blacklisting.
* **500 Internal Server Error:** The target website changed its DOM structure, causing BeautifulSoup to fail. Open an issue on GitHub or paste the stack trace into Claude AI for a hotfix.

---

## 🤝 8. The Official Contribution Protocol

We maintain strict quality control over this repository. If you wish to contribute to the Official Rage AI infrastructure, you must follow this protocol:

1. **Fork the Repository:** Create an isolated copy of the codebase on your account.
2. **Branch Strategy:** Create a semantic branch for your work (e.g., `feature/redis-caching` or `bugfix/search-pagination`).
3. **Write Clean Code:** Ensure your Python code complies with PEP-8 standards. Use type hints for all new functions.
4. **Leverage AI:** Use Claude AI to generate tests for your new endpoints before submitting them.
5. **Commit Semantics:** Use descriptive commit messages (`feat: added support for parsing OBB file sizes`).
6. **Open a Pull Request:** Submit your PR with a detailed explanation of why the change is necessary and what problem it solves.

---

## ⚖️ 9. Software License

This project is distributed under the **BSD 3-Clause License**. This explicitly grants you the freedom to use, modify, and distribute the software, provided that you retain the copyright notice, the list of conditions, and the disclaimer. It expressly prohibits the use of the original authors' or contributors' names to endorse or promote derived products without prior written permission.

See the `LICENSE` file for the full, legally binding text.

<div align="center">
<p><b>Maintained by Official Rage AI</b></p>
<p><i>High-Performance Systems & Scalable Architecture.</i></p>
</div>
