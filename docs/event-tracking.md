# Event Tracking

This document explains how the Flask Ad Server tracks and processes ad events received from the Android SDK.

## Event Types

The server tracks four types of ad events:

1. **view** - User watched the ad to completion
2. **click** - User clicked to visit the advertiser's URL
3. **skip** - User skipped the ad before completion
4. **exit** - User exited the ad without completing or clicking

## Event Data Structure

Events are received as JSON objects with this structure:

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

Where:
- `adId` - The unique identifier for the ad
- `timestamp` - ISO 8601 formatted date and time when the event occurred
- `eventDetails` - Contains:
  - `packageName` - The Android app package name
  - `eventType` - One of: "view", "click", "skip", "exit"
  - `watchDuration` - How long the user watched the ad in seconds

## Event Processing

When an event is received, the server performs these operations:

### 1. Validation

First, the server validates the event data:

```python
# From controller/ad_entrypoints.py
if 'adId' not in data or 'timestamp' not in data or 'eventDetails' not in data:
    return jsonify({'error': 'Missing adId, timestamp or eventDetails'}), 400

ad_id = data['adId']
timestamp = data['timestamp']
event_details = data['eventDetails']

if not isinstance(ad_id, str) or not ad_id.strip():
    return jsonify({'error': 'Invalid adId format'}), 400

required_fields = ['packageName', 'eventType', 'watchDuration']
if not all(field in event_details for field in required_fields):
    return jsonify({'error': 'Missing eventDetails fields'}), 400

package_name = event_details['packageName'].strip()
event_type = event_details['eventType'].strip().lower()
watch_duration = event_details['watchDuration']

VALID_TYPES = {'view', 'click', 'skip', 'exit'}
if event_type not in VALID_TYPES:
    return jsonify({'error': 'Invalid eventType'}), 400
```

### 2. Ad Verification

The server verifies the ad exists in the database:

```python
ad_doc = ads_collection.find_one({'_id': ad_id})
if not ad_doc:
    return jsonify({'error': 'Ad not found'}), 404

performer_id = ad_doc.get('performerId')
if not performer_id:
    return jsonify({'error': 'Ad has no performer assigned'}), 500
```

### 3. Event Storage

The server stores the event in two places:

#### Daily Events Collection

Events are grouped by date for efficient querying:

```python
# Get today's date
today_date = datetime.now(timezone.utc).date().isoformat()

# Create the event document
event_document = {
    "adId": ad_id,
    "performerId": performer_id,
    "packageName": package_name,
    "timestamp": timestamp,
    "eventType": event_type,
    "watchDuration": watch_duration,
    "createdAt": datetime.now(timezone.utc).isoformat()
}

# Store in events_by_day collection
events_by_day_collection.update_one(
    {"date": today_date},
    {"$push": {"events": event_document},
     "$setOnInsert": {"createdAt": datetime.now(timezone.utc).isoformat()}},
    upsert=True
)
```

#### Daily Stats Collection

Events are also aggregated into daily statistics:

```python
# Update daily performer stats
stats_key = {
    "performerId": performer_id,
    "date": today_date
}

inc_fields = {f"counts.{event_type}": 1}
if event_type == "view":
    inc_fields["watchDurationSum"] = watch_duration

daily_stats_collection.update_one(
    stats_key,
    {
        "$inc": inc_fields,
        "$setOnInsert": {
            "adId": ad_id,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    },
    upsert=True
)
```

This approach creates a write-time aggregation that makes analytics queries faster.

## Data Model

### events_by_day Collection

Each document represents all events for a single day:

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

### daily_ad_stats Collection

Each document represents aggregated statistics for a performer on a single day:

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
  "watchDurationSum": 18750.5,
  "adId": "ad-uuid-1",
  "createdAt": "2025-04-30T00:00:00.000Z"
}
```

## Analytics Calculation

The server calculates important metrics from the collected data:

### View Completion Rate

Percentage of ad views that were not skipped or exited:

```
viewCompletionRate = (views / (views + skips + exits)) * 100
```

### Click-Through Rate (CTR)

Percentage of ad views that resulted in clicks:

```
ctr = (clicks / views) * 100
```

### Average Watch Duration

Average time users spent watching the ad:

```
avgWatchDuration = watchDurationSum / views
```

### Conversion Rate

Clicks relative to budget level (simplified model):

```python
BUDGET_LEVELS = {'low': 1, 'medium': 2, 'high': 3}
budget = ad_doc.get('adDetails', {}).get('budget', '').strip().lower()
conv_rate = (clicks / BUDGET_LEVELS.get(budget, 1) * 100) if views else 0
```

## Event Tracking Flow

1. **Event Generation**: The Android SDK generates events when users interact with ads
2. **API Endpoint**: Events are sent to the `/ad_event` endpoint
3. **Validation**: The server validates the event data
4. **Storage**: Events are stored in both raw and aggregated forms
5. **Analytics**: The data is used to calculate performance metrics
6. **Reporting**: The metrics are exposed via the `/ads/<ad_id>/stats` endpoint

## SDK Implementation

On the SDK side, events are generated in the `AdPlayerActivity` class:

```java
// For view events
videoView.setOnCompletionListener(mp -> {
    videoCompleted = true;
    adManager.createEvent(EventEnum.VIEW);
    showEndCard();
});

// For click events
openLinkButton.setOnClickListener(v -> {
    adManager.createEvent(EventEnum.CLICK);
    Intent browserIntent = new Intent(Intent.ACTION_VIEW, Uri.parse(ad.getTargetUrl()));
    startActivity(browserIntent);
    finish();
});

// For skip events
skipButton.setOnClickListener(v -> {
    skipped = true;
    if (!eventSent) {
        adManager.createEvent(EventEnum.SKIP);
        eventSent = true;
    }
    finish();
});

// For exit events (when exiting without completing)
if (!videoCompleted && ad != null) {
    if (!eventSent) {
        adManager.createEvent(EventEnum.EXIT);
        eventSent = true;
    }
    adManager.notifyAdFinished();
}
```

## Debugging Events

For debugging purposes, you can monitor events in these ways:

1. **MongoDB Query**: Examine raw events in the database

    ```javascript
    db.events_by_day.find({"date": "2025-04-30"})
    ```

2. **Date Range Query**: Get events for a specific period

    ```javascript
    db.events_by_day.find({
      "date": {
        "$gte": "2025-04-01", 
        "$lte": "2025-04-30"
      }
    })
    ```

3. **Filter by Package**: Get events for a specific app

    ```javascript
    db.events_by_day.aggregate([
      {$unwind: "$events"},
      {$match: {"events.packageName": "com.example.app"}},
      {$project: {
        "date": 1,
        "event": "$events"
      }}
    ])
    ```
