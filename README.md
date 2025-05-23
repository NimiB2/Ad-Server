# Flask Ad Server – Backend for AdSDK Ecosystem

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Flask](https://img.shields.io/badge/flask-latest-green.svg)
![MongoDB](https://img.shields.io/badge/database-MongoDB%20Atlas-green.svg)

A production-ready Flask backend that powers video advertisement delivery, campaign management, and comprehensive analytics for the AdSDK ecosystem.

## 📚 Documentation & Demo

- **[📖 Complete Documentation](https://nimib2.github.io/video-ad-server/)** - API reference, setup guides, and examples
- **[🎥 Watch Full System Demo](https://NimiB2.github.io/video-ad-server/demo.html)** - See the complete ad system in action

---

## 🚀 Quick Start

### Installation

1. **Clone and setup environment**:
```bash
git clone [your-repo-url]
cd flask-ad-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables**:
Create `.env` file:
```env
DB_CONNECTION_STRING=your-cluster.mongodb.net
DB_NAME=adserver
DB_USERNAME=your-username
DB_PASSWORD=your-password
```

3. **Run the server**:
```bash
python app.py
```
Server starts on `http://localhost:1993`

4. **View API documentation**:
Open `http://localhost:1993/apidocs/` for interactive Swagger docs

---

## 🔧 Core Features

| Feature | Description |
|---------|-------------|
| **Ad Management** | Complete CRUD operations for advertisements |
| **Performer Management** | Advertiser registration and authentication |
| **Smart Ad Delivery** | Random ad selection with package targeting |
| **Event Tracking** | Comprehensive user interaction logging |
| **Real-time Analytics** | Live statistics and performance metrics |
| **Daily Aggregation** | Automated daily statistics compilation |

### Technical Specifications

- **Runtime**: Python 3.9+
- **Framework**: Flask with Flasgger (Swagger)
- **Database**: MongoDB Atlas with optimized indexing
- **API Style**: RESTful with JSON responses
- **Deployment**: Vercel-ready with `vercel.json` configuration

---

## 📋 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/performers` | Create or retrieve performer by email |
| `POST` | `/ads` | Create new advertisement campaign |
| `GET` | `/ads` | Retrieve all advertisements |
| `GET` | `/ads/<id>` | Get specific advertisement |
| `PUT` | `/ads/<id>` | Update advertisement |
| `DELETE` | `/ads/<id>` | Delete advertisement and related data |

### SDK Integration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ads/random?packageName=com.app` | Get random ad for mobile app |
| `POST` | `/ad_event` | Log user interaction events |

### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/ads/<id>/stats` | Get advertisement performance statistics |
| `GET` | `/performers/<id>/stats` | Get performer's aggregated analytics |

### Developer Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/developers/login` | Developer authentication |
| `POST` | `/performers/check-email` | Verify performer email existence |

---

## 🏗️ Architecture

### Core Components

```
Flask Application
├── app.py (Main Application)
├── mongo_db_connection_manager.py (Database Layer)
├── controller/ad_entrypoints.py (API Routes)
└── routes.py (Route Registration)
```

### Database Collections

- **`ads`** - Advertisement metadata and content
- **`performers`** - Advertiser information and campaigns
- **`events_by_day`** - Daily grouped interaction events
- **`daily_ad_stats`** - Aggregated performance metrics
- **`developers`** - System administrator accounts

### Data Flow
1. **Ad Creation** → Performer uploads campaign via API
2. **Ad Delivery** → SDK requests random ad from `/ads/random`
3. **Event Tracking** → User interactions sent to `/ad_event`
4. **Analytics** → Real-time aggregation and reporting

---

## 💡 Implementation Examples

### Ad Creation Request

```python
POST /ads
Content-Type: application/json

{
  "adName": "Summer Sale Campaign",
  "performerEmail": "advertiser@example.com",
  "adDetails": {
    "videoUrl": "https://example.com/video.mp4",
    "targetUrl": "https://example.com/landing",
    "budget": "medium",
    "skipTime": 5.0,
    "exitTime": 30.0
  }
}
```

### Event Tracking Request

```python
POST /ad_event
Content-Type: application/json

{
  "adId": "ad-uuid-123",
  "timestamp": "2025-01-20T10:15:30.000Z",
  "eventDetails": {
    "packageName": "com.example.app",
    "eventType": "view",
    "watchDuration": 15.5
  }
}
```

### Statistics Response

```python
GET /ads/ad-uuid-123/stats?from=2025-01-01&to=2025-01-31

{
  "adId": "ad-uuid-123",
  "dateRange": {"from": "2025-01-01", "to": "2025-01-31"},
  "adStats": {
    "views": 1250,
    "clicks": 75,
    "skips": 350,
    "avgWatchDuration": 15.0,
    "clickThroughRate": 6.0,
    "conversionRate": 75.0
  }
}
```

---

## 🔗 Integration with Ecosystem

The Flask server integrates with:

- **[Android SDK](https://nimib2.github.io/video-ad-sdk-android/)** - Mobile ad delivery and tracking
- **[Ad Portal](https://nimib2.github.io/video-ad-portal/)** - Web-based campaign management
- **MongoDB Atlas** - Cloud database with automated scaling

---

## 🚀 Deployment

### Vercel Deployment

The project includes `vercel.json` for seamless deployment:

```json
{
  "version": 2,
  "builds": [{"src": "app.py", "use":"@vercel/python"}],
  "routes": [{"src": "/(.*)", "dest":"app.py"}]
}
```

Deploy with:
```bash
vercel
```

### Environment Configuration

Set these variables in your deployment platform:
```
DB_CONNECTION_STRING=your-mongodb-atlas-url
DB_NAME=your-database-name
DB_USERNAME=your-db-username
DB_PASSWORD=your-db-password
```

---

## 📖 Additional Resources

- **[Server Setup Guide](https://nimib2.github.io/video-ad-server/server-setup.html)** - Detailed installation instructions
- **[Database Schema](https://nimib2.github.io/video-ad-server/database-schema.html)** - Collection structure and relationships
- **[Event Tracking](https://nimib2.github.io/video-ad-server/event-tracking.html)** - Analytics implementation details
- **[SDK Support](https://nimib2.github.io/video-ad-server/sdk-support.html)** - Android integration guide

---

## ✨ What's New

### Current Version
- **Email Validation** - Built-in performer email verification
- **Advanced Analytics** - Date-filtered statistics with aggregation
- **Developer Authentication** - Separate admin access system
- **Enhanced Error Handling** - Comprehensive validation and responses
- **Optimized Indexing** - MongoDB performance improvements
- **Comprehensive Swagger Documentation** - Interactive API exploration

---

## 📄 License

**This is an educational study project created for learning purposes only.**
Demo content and advertisements are used for demonstration and are not intended for commercial use.

```
MIT License

Copyright (c) 2025 Nimrod Bar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```
