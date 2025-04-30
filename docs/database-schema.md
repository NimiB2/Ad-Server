---
layout: default
title: Database Schema
parent: Server Documentation
nav_order: 3
permalink: /server/database-schema/
---
# Database Schema

The Flask Ad Server uses MongoDB to store ads, performers, and event tracking data. This document outlines the collection structure and relationships.

## Connection Management

Database connections are managed by the `MongoConnectionManager` class in `mongo_db_connection_manager.py`, which implements a singleton pattern to maintain a single database connection across the application.

```python
# Environment variables used for connection
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")
DB_NAME = os.getenv("DB_NAME")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")

Mongo_URI = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@{DB_CONNECTION_STRING}/{DB_NAME}"
```

## Collections

The database consists of the following collections:

### performers

Stores information about ad creators/advertisers.

```javascript
{
  "_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479", // UUID string
  "name": "John Smith",
  "email": "john.smith@example.com",
  "ads": ["ad-uuid-1", "ad-uuid-2"] // References to ad IDs
}
```

### ads

Stores ad metadata and content.

```javascript
{
  "_id": "ad-uuid-1", // UUID string
  "name": "My Ad Campaign",
  "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "performerName": "John Smith",
  "adDetails": {
    "videoUrl": "https://example.com/video.mp4",
    "targetUrl": "https://example.com/landing",
    "budget": "low", // "low", "medium", or "high"
    "skipTime": 5.0, // Seconds before skip button appears
    "exitTime": 30.0 // Seconds before exit button appears
  },
  "createdAt": "2025-04-30T10:00:00.000Z",
  "updatedAt": "2025-04-30T10:00:00.000Z"
}
```

### ad_events

Stores individual ad interaction events.

```javascript
{
  "adId": "ad-uuid-1",
  "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "packageName": "com.example.app",
  "timestamp": "2025-04-30T10:15:30.000Z",
  "eventType": "view", // "view", "click", "skip", or "exit"
  "watchDuration": 15.5, // Seconds the ad was watched
  "createdAt": "2025-04-30T10:15:30.000Z"
}
```

### events_by_day

Stores events grouped by date for efficient querying.

```javascript
{
  "date": "2025-04-30",
  "events": [
    {
      "adId": "ad-uuid-1",
      "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "packageName": "com.example.app",
      "timestamp": "2025-04-30T10:15:30.000Z",
      "eventType": "view",
      "watchDuration": 15.5,
      "createdAt": "2025-04-30T10:15:30.000Z"
    },
    // More events...
  ],
  "createdAt": "2025-04-30T00:00:00.000Z"
}
```

### daily_ad_stats

Contains aggregated daily statistics for efficient reporting.

```javascript
{
  "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "date": "2025-04-30",
  "counts": {
    "view": 1250,
    "click": 75,
    "skip": 350,
    "exit": 825
  },
  "watchDurationSum": 18750.5, // Total seconds watched
  "adId": "ad-uuid-1", // For reference
  "createdAt": "2025-04-30T00:00:00.000Z"
}
```

## Indexes

The server automatically creates an index for daily statistics during initialization:

```python
# Create index for daily stats
try:
    daily_stats_collection.create_index(
        [("performerId", 1), ("date", 1)],
        unique=True,
        name="uniq_performer_date"
    )
except Exception as _idx_err:
    print(f"[Init] daily_performer_stats index skipped/failed: {_idx_err}")
```

This index ensures efficient querying of daily performance metrics by performer and date.

## Data Relationships

The database implements the following relationships:

1. **Performer to Ads** (One-to-Many):
   - Performer documents contain an array of ad IDs
   - Ad documents contain a performerId reference

2. **Ad to Events** (One-to-Many):
   - Events contain the adId they relate to
   - Daily statistics are aggregated by adId and performerId

## Database Operations

Common operations include:

- Finding ads that haven't been shown to a specific app package:
  ```python
  # Find ad IDs that have appeared for this package_name
  pipeline = [
      {'$match': {'events.packageName': package_name}},
      {'$unwind': '$events'},
      {'$match': {'events.packageName': package_name}},
      {'$group': {'_id': '$events.adId'}}
  ]
  
  appeared_ad_ids = [doc['_id'] for doc in events_by_day_collection.aggregate(pipeline)]
  
  unappeared_ads = list(
      ads_collection.find({'_id': {'$nin': appeared_ad_ids}})
  )
  ```

- Aggregating statistics for reporting:
  ```python
  pipeline = [
      {'$match': match},
      {'$group': {
          '_id': '$adId',
          'views':  {'$sum': '$counts.view'},
          'clicks': {'$sum': '$counts.click'},
          'skips':  {'$sum': '$counts.skip'},
          'exits':  {'$sum': '$counts.exit'},
          'watchDurationSum': {'$sum': '$watchDurationSum'}
      }}
  ]
  
  agg = list(daily_stats_collection.aggregate(pipeline))
  ```
