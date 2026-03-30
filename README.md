# ====================== APKDone API - ALL FILES ======================

## 1. README.md
```markdown
# APKDone API

[<image-card alt="Python" src="https://img.shields.io/badge/Python-3.11+-blue.svg" ></image-card>](https://www.python.org/)
[<image-card alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115+-green.svg" ></image-card>](https://fastapi.tiangolo.com/)

**A lightweight FastAPI wrapper/scraper for APKDone.com**

## 🚨 Important Notice
**This project is made for educational purposes only.**

It is intended **solely for learning** web scraping, FastAPI development, async HTTP handling, BeautifulSoup parsing, rate limiting, and API design.

**Do not use it for commercial purposes or in any way that violates the terms of service of APKDone.com or ScraperAPI.com.**

Use at your own risk. The author is not responsible for any misuse or legal issues.

## 🔑 ScraperAPI Integration
This API uses **[ScraperAPI](https://scraperapi.com/)** to bypass anti-bot protection, CAPTCHA, and IP blocks when scraping APKDone.com.

- All scraping requests go through ScraperAPI’s proxy service.
- You **must** add your own `SCRAPER_API_KEY` in the `.env` file or as an environment variable.
- Without a valid key, the API will not work.

## ✨ Features & Endpoints

| Method | Endpoint                  | Description                                      | Rate Limit     | Parameters                  |
|--------|---------------------------|--------------------------------------------------|----------------|-----------------------------|
| GET    | `/`                       | Root – shows welcome message and available routes| None           | -                           |
| GET    | `/home`                   | Featured, New & Popular apps from homepage       | 10/min         | -                           |
| GET    | `/trending`               | Trending / Most-downloaded apps                  | 10/min         | -                           |
| GET    | `/games`                  | All Games category (supports pagination)         | 10/min         | `page` (optional)           |
| GET    | `/categories`             | List of all app categories                       | 10/min         | -                           |
| GET    | `/category/{slug}`        | Apps in a specific category                      | 10/min         | `page` (optional)           |
| GET    | `/search`                 | Search apps by keyword                           | 10/min         | `q` (required)              |
| GET    | `/app`                    | Full app details + download links                | 10/min         | `url` (required)            |

All endpoints return clean JSON with proper error handling.

## 🛠 Tech Stack & Code Details

- **Framework**: FastAPI (async)
- **HTTP Client**: httpx (async requests via ScraperAPI)
- **Parser**: BeautifulSoup4 + lxml
- **Rate Limiter**: SlowAPI (10 requests per minute per IP)
- **CORS**: Enabled for all origins
- **Environment**: python-dotenv

**Main files**:
- `app.py` → Contains all routes and scraping logic
- `requirements.txt` → List of dependencies

## 🚀 Local Development

```bash
# 1. Clone or Fork the repo
git clone https://github.com/raihanbhaii/apkdone-API.git
cd apkdone-API

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate          # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
echo "SCRAPER_API_KEY=your_scraperapi_key_here" > .env

# 5. Run the server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
