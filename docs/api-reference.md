---
layout: default
title: API Reference
nav_order: 2
---
# API Reference

This document provides detailed information about the available API endpoints in the Flask Ad Server.

## Base URL

The API is hosted at:

```
https://ad-server-kappa.vercel.app/
```

## Authentication

Currently, the API does not implement authentication. This may change in future versions.

## Endpoints

### Performers

#### Create Performer

Creates a new performer or returns an existing performer by email.

- **URL**: `/performers`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body**:

```json
{
  "name": "John Smith",
  "email": "john.smith@example.com"
}
```

**Response**:

- **201 Created** - Performer created successfully
  ```json
  {
    "message": "Performer created",
    "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
  ```

- **200 OK** - Performer already exists
  ```json
  {
    "message": "Performer already exists",
    "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
  }
  ```

- **400 Bad Request** - Invalid input or email format
  ```json
  {
    "error": "Invalid email format"
  }
  ```

### Ads

#### Create Ad

Creates a new ad for a performer.

- **URL**: `/ads`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body**:

```json
{
  "adName": "My Ad Campaign",
  "performerEmail": "performer@example.com",
  "adDetails": {
    "videoUrl": "https://example.com/video.mp4",
    "targetUrl": "https://example.com/landing",
    "budget": "low",
    "skipTime": 5.0,
    "exitTime": 30.0
  }
}
```

**Response**:

- **201 Created** - Ad created successfully
  ```json
  {
    "message": "Ad created successfully",
    "adId": "ad-uuid-1"
  }
  ```

- **400 Bad Request** - Invalid request
- **404 Not Found** - Performer not found
- **500 Internal Server Error** - Server error

#### Get All Ads

Returns a list of all ads.

- **URL**: `/ads`
- **Method**: `GET`

**Response**:

- **200 OK** - List of ads returned
- **500 Internal Server Error** - Server error

#### Get Ad by ID

Returns a specific ad by ID.

- **URL**: `/ads/{ad_id}`
- **Method**: `GET`

**Response**:

- **200 OK** - Ad returned
- **404 Not Found** - Ad not found
- **500 Internal Server Error** - Server error

#### Update Ad

Updates an existing ad.

- **URL**: `/ads/{ad_id}`
- **Method**: `PUT`
- **Content-Type**: `application/json`

**Request Body**:
Any fields to update in the ad object.

**Response**:

- **200 OK** - Ad updated
- **404 Not Found** - Ad not found
- **400 Bad Request** - Invalid request
- **500 Internal Server Error** - Server error

#### Delete Ad

Deletes an ad.

- **URL**: `/ads/{ad_id}`
- **Method**: `DELETE`

**Response**:

- **200 OK** - Ad deleted
- **404 Not Found** - Ad not found
- **500 Internal Server Error** - Server error

#### Get Random Ad

Returns a random ad for an app to display.

- **URL**: `/ads/random`
- **Method**: `GET`
- **Query Parameters**:
  - `packageName` (required) - Package name of the requesting app

**Response**:

- **200 OK** - Random ad returned
- **204 No Content** - No ads available
- **400 Bad Request** - Missing packageName parameter
- **500 Internal Server Error** - Server error

### Event Tracking

#### Send Ad Event

Logs an ad event (view, click, skip, exit).

- **URL**: `/ad_event`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body**:

```json
{
  "adId": "ad-uuid-1",
  "timestamp": "2025-04-30T10:15:30.000Z",
  "eventDetails": {
    "packageName": "com.example.app",
    "eventType": "view",
    "watchDuration": 15.5
  }
}
```

**Response**:

- **201 Created** - Event logged successfully
- **400 Bad Request** - Invalid request
- **404 Not Found** - Ad not found
- **500 Internal Server Error** - Server error

### Analytics

#### Get Ad Statistics

Get aggregated statistics for an ad.

- **URL**: `/ads/{ad_id}/stats`
- **Method**: `GET`
- **Query Parameters**:
  - `from` (optional) - Inclusive start date (YYYY-MM-DD)
  - `to` (optional) - Inclusive end date (YYYY-MM-DD)

**Response**:

- **200 OK** - Statistics returned
  ```json
  {
    "adId": "ad-uuid-1",
    "dateRange": {
      "from": "2025-04-01",
      "to": "2025-04-30"
    },
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

- **404 Not Found** - Ad not found
- **500 Internal Server Error** - Server error

#### Get Performer Statistics

Get statistics for all ads of a performer.

- **URL**: `/performers/{performer_id}/stats`
- **Method**: `GET`

**Response**:

- **200 OK** - Statistics returned
  ```json
  {
    "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "adsStats": [
      {
        "adId": "ad-uuid-1",
        "views": 1250,
        "clicks": 75,
        "skips": 350,
        "exits": 825,
        "avgWatchDuration": 15.0,
        "clickThroughRate": 6.0
      },
      {
        "adId": "ad-uuid-2",
        "views": 850,
        "clicks": 42,
        "skips": 230,
        "exits": 578,
        "avgWatchDuration": 12.5,
        "clickThroughRate": 4.9
      }
    ]
  }
  ```

- **404 Not Found** - Performer not found
- **500 Internal Server Error** - Server error

## Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "Error message describing the issue"
}
```

## Swagger Documentation

The API includes Swagger documentation accessible at `/apidocs/` on the server. This provides an interactive way to explore and test the API endpoints.
