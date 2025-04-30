---
layout: default
title: SDK Support
parent: Server Documentation
nav_order: 6
permalink: /server/sdk-support/
---
# SDK Support

This document explains how the Flask Ad Server supports the Android AdSDK and the communication between the two components.

## Integration Overview

The Android AdSDK communicates with the Flask server through a RESTful API. The server provides the following essential functions to the SDK:

1. **Ad Delivery** - Providing ad content to display
2. **Event Tracking** - Recording user interactions with ads
3. **Reporting** - Aggregating and analyzing ad performance

## API Endpoints for SDK

The SDK primarily uses these endpoints:

### 1. Random Ad Request

```
GET /ads/random?packageName=com.example.app
```

This endpoint is called by the AdController in the SDK when:
- The SDK is initialized with `AdSdk.init()`
- The preload manager needs to fetch the next ad

The server selects an appropriate ad based on:
- Package name of the requesting app
- Ad visibility history (prioritizing ads not yet seen by this app)
- Budget levels and other targeting criteria

```python
# From controller/ad_entrypoints.py
@ad_routes_blueprint.route('/ads/random', methods=['GET'])
def get_random_ad():
    package_name = request.args.get('packageName')
    
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
    if not unappeared_ads:
        unappeared_ads = list(ads_collection.find())
        if not unappeared_ads:
            return jsonify({'message': 'No ads available'}), 204

    chosen_ad = random.choice(unappeared_ads)
    chosen_ad['_id'] = str(chosen_ad['_id'])
    return jsonify(chosen_ad), 200
```

### 2. Event Tracking

```
POST /ad_event
```

The SDK calls this endpoint to record various events:
- VIEW - User watched the ad to completion
- CLICK - User clicked to visit the advertiser's URL
- SKIP - User skipped the ad before completion
- EXIT - User exited the ad

The AdController in the SDK sends these events with details:

```java
// AdController.java
public void sendAdEvent(String adId, String packageName, String eventType, float watchDuration) {
    if (adId == null) {
        Log.e(TAG, "Cannot send event: ad ID is null");
        return;
    }

    try {
        Event event = new Event();
        event.setAdId(adId);
        // Set timestamp for current time in ISO 8601 format
        SimpleDateFormat isoFormat = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'", Locale.US);
        isoFormat.setTimeZone(TimeZone.getTimeZone("UTC"));
        event.setTimestamp(isoFormat.format(new Date()));

        Event.EventDetails details = new Event.EventDetails();
        details.setPackageName(packageName);
        details.setEventType(eventType);
        details.setWatchDuration(watchDuration);

        event.setEventDetails(details);

        Log.d(TAG, "Sending event: " + new Gson().toJson(event));

        AdApiService apiService = getApiService();
        Call<Void> call = apiService.sendAdEvent(event);

        call.enqueue(new Callback<Void>() {
            @Override
            public void onResponse(Call<Void> call, Response<Void> response) {
                if (response.isSuccessful()) {
                    Log.d(TAG, "Event sent successfully: " + eventType);
                } else {
                    Log.e(TAG, "Error sending event: " + response.code());
                }
            }

            @Override
            public void onFailure(Call<Void> call, Throwable t) {
                Log.e(TAG, "Failure sending event", t);
            }
        });
    } catch (Exception e) {
        Log.e(TAG, "Error sending event", e);
    }
}
```

The server processes these events to:
- Record individual events
- Update daily aggregations
- Calculate statistics like click-through rates

```python
# From controller/ad_entrypoints.py
@ad_routes_blueprint.route('/ad_event', methods=['POST'])
def send_ad_event():
    data = request.json
    # Validation logic omitted for brevity
    
    # Store in events_by_day collection
    events_by_day_collection.update_one(
        {"date": today_date},
        {"$push": {"events": event_document},
         "$setOnInsert": {"createdAt": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
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

## Data Flow

The full data flow between the SDK and server:

1. **Initialization**:
   - SDK requests an ad from `/ads/random`
   - Server selects and returns an appropriate ad
   - SDK stores the ad and notifies the app it's ready

2. **Display**:
   - App calls `AdSdk.showAd()`
   - SDK displays the ad and begins tracking watch time
   - User interacts with the ad (watches, clicks, skips, or exits)

3. **Event Reporting**:
   - SDK sends event data to `/ad_event`
   - Server records the event and updates aggregations
   - SDK notifies the app of completion via callback

4. **Preloading**:
   - SDK begins loading the next ad in the background
   - The cycle repeats

## API Models

The SDK and server exchange data using these model structures:

### Ad Model

```java
// Ad.java (SDK side)
public class Ad {
    private String id;
    private String performerName;
    private String adName;
    private AdDetails adDetails;
    private String performerEmail;
    
    // AdDetails contains:
    // - videoUrl
    // - targetUrl
    // - budget
    // - skipTime
    // - exitTime
}
```

Corresponds to the server model:

```python
# Server side (in JSON response)
{
    "_id": "ad-uuid-1",
    "name": "My Ad Campaign",
    "performerId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    "performerName": "John Smith",
    "adDetails": {
        "videoUrl": "https://example.com/video.mp4",
        "targetUrl": "https://example.com/landing",
        "budget": "low",
        "skipTime": 5.0,
        "exitTime": 30.0
    }
}
```

### Event Model

```java
// Event.java (SDK side)
public class Event {
    private String adId;
    private String timestamp;
    private EventDetails eventDetails;
    
    // EventDetails contains:
    // - packageName
    // - eventType
    // - watchDuration
}
```

Corresponds to the server event model:

```python
# Server side (from JSON request)
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

## Server Configuration for SDK Support

For optimal support of the Android SDK, the server should be configured with:

1. **Sufficient capacity** - To handle concurrent requests
2. **Low latency** - To provide quick ad delivery
3. **High availability** - To ensure ads are always accessible
4. **Regular monitoring** - To identify and address issues

See the [Server Setup](server-setup.md) guide for detailed deployment instructions.
