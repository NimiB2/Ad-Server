---
layout: default
title: Home
nav_order: 1
---
# Flask Ad Server Documentation

## Overview

The Flask Ad Server is the backend component that powers the AdSDK ecosystem. It handles ad management, delivery, and analytics tracking through a RESTful API interface.

## Documentation Sections

- [Server Setup](server-setup.md) - Installation and deployment guide
- [Database Schema](database-schema.md) - MongoDB collections and structure
- [API Reference](api-reference.md) - Complete endpoint documentation
- [Event Tracking](event-tracking.md) - How ad events are processed
- [Analytics](analytics.md) - Statistics and reporting
- [SDK Support](sdk-support.md) - How the server supports the Android SDK

## Core Components

The Flask Ad Server consists of these primary components:

### Main Application (app.py)
The entry point of the Flask application that initializes the database connection, registers routes, and configures Swagger documentation.

### MongoDB Connection (mongo_db_connection_manager.py)
Manages the connection to MongoDB Atlas with the following features:
- Singleton pattern for database access
- Environment-based configuration
- Connection pooling

### Ad Endpoints (controller/ad_entrypoints.py)
Contains all API routes for managing ads:
- `POST /performers` - Create/fetch performers
- `POST /ads` - Create new ads
- `GET /ads/random` - Get a random ad for display
- `POST /ad_event` - Track ad events (view, click, skip, exit)
- `GET /ads/<ad_id>/stats` - Get statistics for a specific ad
- `GET /performers/<performer_id>/stats` - Get statistics for a performer

### Route Initialization (routes.py)
Registers the ad blueprint with the main application.

## Database Collections

- `ads` - Stores ad metadata and content
- `performers` - Stores advertiser information
- `ad_events` - Tracks individual ad events
- `daily_ad_stats` - Aggregated daily statistics
- `events_by_day` - Events grouped by date

## Related Documentation

For the client-side SDK that consumes this API, see the [Android AdSDK Documentation](https://nimib2.github.io/Android-SDK-Ads/).
