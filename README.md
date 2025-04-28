# Flask Ad Server – Backend for AdSDK

## Overview
The **Flask Ad Server** is a lightweight RESTful backend that powers campaign management, ad delivery, and analytics for the AdSDK ecosystem.  
It exposes secure endpoints for advertisers to upload creatives, retrieve real‑time statistics, and for the SDK to request ads and log events.

> **Note**  
> This README focuses solely on the Flask backend.  
> Android integration details live in the [AdSDK library README](../README.md).

---

### Project Architecture

The Ad SDK system consists of several interconnected components that work together to deliver ads to mobile applications:


<div align="center">
    <img src="https://github.com/user-attachments/assets/e4b1569d-e86d-41d7-a824-c2f7c30b42f0" alt="Project Image" width="320"/>
</div>

---

## Documentation
Interactive Swagger docs are generated automatically at **`/apidocs/`** once the server is running.

---

## Features

- **Advertiser & Ad CRUD** – create performers, upload ads, and manage campaigns.
- **Random Ad Selection** – returns ads matched to a package name or globally when no match is found.
- **Event Logging** – endpoints for **view**, **click**, **skip**, and **exit** events.
- **Daily Aggregation** – scheduled summarisation into a `daily_ad_stats` collection.
- **Analytics Endpoints** – fine‑grained stats per ad or performer.
- **Swagger UI** – auto‑generated API exploration via **Flasgger**.

---

## Tech Stack
- **Python 3.12** & **Flask** – REST API framework.
- **MongoDB Atlas** – document database with indexes for fast aggregation.
- **Flasgger** – Swagger/OpenAPI documentation.
- **python-dotenv** – environment configuration.

---

## Quick Start

1. **Clone the repo** and change directory:
   ```bash
   git clone https://github.com/your-user/AdSDK.git
   cd AdSDK/flask-ad-server
   ```
2. **Create and activate a virtual env** (optional but recommended):
   ```bash
   python -m venv .venv && source .venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables** – copy `.env.example` to `.env` and fill in your Atlas URI and DB credentials.
5. **Run the app**:
   ```bash
   flask --app app run --port 1993  # defaults: 127.0.0.1:1993
   ```
6. **Browse docs**: open <http://localhost:1993/apidocs/>.

---

## Key API Endpoints
| Method | Path | Purpose |
| ------ | ------------------------------- | --------------------------------------------- |
| `POST` | `/performers` | Create or fetch a performer (by email). |
| `POST` | `/ads` | Upload a new ad for a performer. |
| `GET`  | `/ads/random?packageName=com.app` | Serve a random eligible ad. |
| `POST` | `/ad_event` | Log ad events (*view, click, skip, exit*). |
| `GET`  | `/ads/<ad_id>/stats` | Stats for a single ad. |
| `GET`  | `/performers/<perf_id>/stats` | Aggregated stats for one performer. |

Further details—including payload schemas—are visible in Swagger.

---

## Deployment Notes
- **Render / Vercel** – compatible with container‑based PaaS; just set env vars and expose port `1993`.
- **Indexes** – the app auto‑creates compound indexes for aggregation on first run.
- **Scaling** – shard by `performerId` in Atlas for high‑volume traffic.

---

## License
See the root project license. Backend usage is governed by the same terms as the AdSDK.

