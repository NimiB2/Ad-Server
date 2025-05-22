# Flask Ad Server – Backend for AdSDK

## Overview
The **Flask Ad Server** is a lightweight RESTful backend that powers campaign management, ad delivery, and analytics for the AdSDK ecosystem.  
It exposes secure endpoints for advertisers to upload creatives, retrieve real‑time statistics, and for the SDK to request ads and log events.

---

### Project Architecture

The Ad SDK system consists of several interconnected components that work together to deliver ads to mobile applications:


<div align="center">
    <img src="https://github.com/user-attachments/assets/e4b1569d-e86d-41d7-a824-c2f7c30b42f0" alt="Project Image" width="360"/>
</div>

---

## 📱 AdSDK – Watch How It Works

<a href="https://github.com/NimiB2/video-ad-server/releases/download/v1.0/AdSdkPlatform_V2.mp4">
  <img src="https://i.imgur.com/BarqWRo.png" alt="AdSDK Demo" width="200"/>
</a>

---

## Documentation

For detailed documentation, visit [AdSDK Documentation](https://nimib2.github.io/video-ad-server/).

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

MIT License - Copyright © 2025 Nimrod Bar

This study project is created for educational purposes only. Demo content is not for commercial use.

Permission is granted to use, copy, modify, and distribute this software subject to including the above copyright notice and permission notice in all copies.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

[Full license](https://opensource.org/licenses/MIT)

---
