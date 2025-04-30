---
layout: default
title: Analytics
parent: Server Documentation
nav_order: 5
permalink: /server/analytics/
---
# Analytics

This document explains the analytics capabilities of the Flask Ad Server, including data collection, processing, and reporting.

## Analytics Overview

The ad server collects and processes events from the AdSDK to provide insights into ad performance. Key metrics include:

- View counts
- Click-through rates (CTR)
- Skip rates
- Watch duration
- Conversion rates

## Data Collection

Analytics data is collected through the `/ad_event` endpoint. The server receives events in this format:

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

These events are processed and stored in two ways:

1. **Raw Events**: Stored in the `events_by_day` collection, grouped by date
2. **Aggregated Stats**: Summarized in the `daily_ad_stats` collection

## Reporting Endpoints

The server provides two main reporting endpoints:

### 1. Ad Statistics

```
GET /ads/<ad_id>/stats
```

**Optional Query Parameters:**
- `from`: Start date (YYYY-MM-DD)
- `to`: End date (YYYY-MM-DD)

**Sample Response:**
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

### 2. Performer Statistics

```
GET /performers/<performer_id>/stats
```

**Sample Response:**
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

## Metric Calculations

The server calculates these metrics using MongoDB aggregation pipelines:

### View Stats

Basic view counts are straightforward sums:

```python
pipeline = [
    {'$match': match},
    {'$group': {
        '_id': '$adId',
        'views': {'$sum': '$counts.view'},
        'clicks': {'$sum': '$counts.click'},
        'skips': {'$sum': '$counts.skip'},
        'exits': {'$sum': '$counts.exit'},
        'watchDurationSum': {'$sum': '$watchDurationSum'}
    }}
]
```

### Click-Through Rate (CTR)

Percentage of ad views that resulted in clicks:

```python
views = totals['views']
clicks = totals['clicks']
ctr = (clicks / views * 100) if views else 0
```

### Average Watch Duration

Average time users spent watching the ad:

```python
views = totals['views']
watch_sum = totals['watchDurationSum']
avg_watch = watch_sum / views if views else 0
```

### Conversion Rate

A budget-weighted metric that evaluates ad effectiveness:

```python
BUDGET_LEVELS = {'low': 1, 'medium': 2, 'high': 3}
budget = ad_doc.get('adDetails', {}).get('budget', '').strip().lower()
conv_rate = (clicks / BUDGET_LEVELS.get(budget, 1) * 100) if views else 0
```

## MongoDB Aggregation

The server uses MongoDB's aggregation framework for efficient analytics:

```python
# Example: Finding ads not yet shown to a package
pipeline = [
    {'$match': {'events.packageName': package_name}},
    {'$unwind': '$events'},
    {'$match': {'events.packageName': package_name}},
    {'$group': {'_id': '$events.adId'}}
]

appeared_ad_ids = [doc['_id'] for doc in events_by_day_collection.aggregate(pipeline)]
```

## Date Filtering

For date-based analytics, the server supports date range filters:

```python
match = {'adId': ad_id}
date_from = request.args.get('from') 
date_to = request.args.get('to')

if date_from or date_to:
    match['date'] = {}
    if date_from:
        match['date']['$gte'] = date_from
    if date_to:
        match['date']['$lte'] = date_to
```

## Performance Considerations

The analytics system uses several optimizations:

1. **Daily Aggregation**: Events are pre-aggregated by day at write time
2. **Compound Indexes**: The collections have indexes for efficient querying:
   ```python
   daily_stats_collection.create_index(
       [("performerId", 1), ("date", 1)],
       unique=True,
       name="uniq_performer_date"
   )
   ```
3. **Projection**: Queries include only necessary fields

## Extending Analytics

To extend the analytics capabilities:

### Adding New Metrics

1. Add the metric to the aggregation pipeline:
   ```python
   pipeline = [
       # ... existing pipeline ...
       {'$project': {
           # ... existing fields ...
           'newMetric': {'$divide': ['$clicks', '$totalEngagements']}
       }}
   ]
   ```

2. Include the new metric in the response:
   ```python
   return jsonify({
       # ... existing fields ...
       'newMetric': result['newMetric']
   })
   ```

### Creating Custom Reports

Create a new endpoint with custom aggregation:

```python
@ad_routes_blueprint.route('/custom_report', methods=['GET'])
def custom_report():
    # Custom aggregation pipeline
    pipeline = [
        # Custom stages
    ]
    
    results = daily_stats_collection.aggregate(pipeline)
    return jsonify(list(results))
```

## Data Visualization

While the server doesn't include a visualization interface, the JSON responses are designed to be easily consumed by visualization tools like:

- Tableau
- Power BI
- Custom dashboards with Chart.js, D3.js, etc.

To integrate with these tools:
1. Create an application to fetch data from the API endpoints
2. Transform the data if needed
3. Pass it to your visualization framework

## Related Documentation

For more details on:
- How events are tracked: [Event Tracking](event-tracking.md)
- Database structure: [Database Schema](database-schema.md)
- SDK integration: [SDK Support](sdk-support.md)
