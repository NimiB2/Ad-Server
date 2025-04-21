from flask import request, jsonify, Blueprint
from mongo_db_connection_manager import MongoConnectionManager
import random
from datetime import datetime, timezone
import uuid

ad_routes_blueprint = Blueprint('ads', __name__)

db = MongoConnectionManager.get_db()
ads_collection = db['ads']
performers_collection = db['performers']
events_collection = db['ad_events']

@ad_routes_blueprint.route('/performers', methods=['POST'])
def create_performer():
    """
    Create or return an existing performer by email
    ---
    parameters:
      - name: performer
        in: body
        required: true
        description: The performer to create
        schema:
          id: Performer
          required:
            - name
            - email
          properties:
            name:
              type: string
            email:
              type: string
    responses:
      201:
        description: Performer created successfully
      200:
        description: Performer already exists, returned existing ID
      400:
        description: Invalid input
      500:
        description: Internal server error
    """
    data = request.json
    required_fields = ['name', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing name or email'}), 400

    name = data['name'].strip()
    email = data['email'].strip()
    if not name or not email:
        return jsonify({'error': 'Name and email cannot be empty'}), 400

    existing = performers_collection.find_one({'email': email})
    if existing:
        return jsonify({
            'message': 'Performer already exists',
            'performerId': existing['_id']
        }), 200

    performer = {
        "_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "ads": []
    }

    try:
        performers_collection.insert_one(performer)
        return jsonify({'message': 'Performer created', 'performerId': performer['_id']}), 201
    except Exception as e:
        return jsonify({'error': 'Failed to create performer'}), 500

# Create new ad
@ad_routes_blueprint.route('/ads', methods=['POST'])
def create_ad():
    """
    Create a new ad (using performer email instead of ID)
    ---
    parameters:
      - name: ad
        in: body
        required: true
        description: The ad to create
        schema:
          id: Ad
          required:
            - adName
            - adDetails
            - email
          properties:
            adName:
              type: string
              description: The name of the ad
            email:
              type: string
              description: Email of the performer who owns the ad
            adDetails:
              type: object
              properties:
                videoUrl:
                  type: string
                targetUrl:
                  type: string
                budget:
                  type: string
                  enum: [low, medium, high]
                skipTime:
                  type: number
                  format: float
                exitTime:
                  type: number
                  format: float
    responses:
      201:
        description: Ad created successfully
      400:
        description: Invalid request
      404:
        description: Performer not found
      500:
        description: Internal server error
    """
    ad_data = request.json

    required_fields = ['adName', 'email', 'adDetails']
    if not all(field in ad_data for field in required_fields):
        return jsonify({'error': 'Missing required fields (adName, email, adDetails)'}), 400

    email = ad_data['email'].strip()
    performer = performers_collection.find_one({'email': email})
    if not performer:
        return jsonify({'error': 'Performer not found'}), 404

    performer_id = performer['_id']
    name = ad_data['adName']
    ad_details = ad_data['adDetails']

    # Validation for adDetails
    required_details = ['videoUrl', 'targetUrl', 'budget', 'skipTime', 'exitTime']
    if not all(field in ad_details for field in required_details):
        return jsonify({'error': 'Missing adDetails fields'}), 400

    video_url = ad_details['videoUrl'].strip()
    target_url = ad_details['targetUrl'].strip()
    budget = ad_details['budget'].strip().lower()
    try:
        skip_time = float(ad_details['skipTime'])
        exit_time = float(ad_details['exitTime'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid skipTime or exitTime'}), 400

    if not video_url.startswith("http") or not target_url.startswith("http"):
        return jsonify({'error': 'Invalid URLs'}), 400

    if budget not in {"low", "medium", "high"}:
        return jsonify({'error': 'Invalid budget'}), 400

    ad = {
        "_id": str(uuid.uuid4()),
        "name": name.strip(),
        "performerId": performer_id,
        "adDetails": {
            "videoUrl": video_url,
            "targetUrl": target_url,
            "budget": budget,
            "skipTime": skip_time,
            "exitTime": exit_time
        },
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }

    try:
        ads_collection.insert_one(ad)
        performers_collection.update_one(
            {'_id': performer_id},
            {'$addToSet': {'ads': ad['_id']}}
        )
        return jsonify({'message': 'Ad created successfully', 'adId': ad['_id']}), 201
    except Exception:
        return jsonify({'error': 'Failed to create ad'}), 500

# Get all ads
@ad_routes_blueprint.route('/ads', methods=['GET'])
def get_all_ads():
    """
Get all ads
---
responses:
  200:
    description: A list of all ads was returned successfully
  500:
    description: An error occurred while retrieving ads
    """
    try:
        ads = list(ads_collection.find())
        for ad in ads:
            ad['_id'] = str(ad['_id'])
        return jsonify(ads), 200
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve ads'}), 500

# Get one ad by id
@ad_routes_blueprint.route('/ads/<ad_id>', methods=['GET'])
def get_ad_by_id(ad_id):
    """
Get an ad by ID
---
parameters:
  - name: ad_id
    in: path
    type: string
    required: true
    description: The ID of the ad to retrieve
responses:
  200:
    description: The ad was returned successfully
  404:
    description: Ad not found
  500:
    description: An error occurred while retrieving the ad
    """

    try:
        ad = ads_collection.find_one({'_id': ad_id})
        if ad:
            ad['_id'] = str(ad['_id'])
            return jsonify(ad), 200
        return jsonify({'error': 'Ad not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve ad'}), 500

# Update ad
@ad_routes_blueprint.route('/ads/<ad_id>', methods=['PUT'])
def update_ad(ad_id):
    """
Update an existing ad
---
parameters:
  - name: ad_id
    in: path
    type: string
    required: true
    description: The ID of the ad to update
  - name: ad
    in: body
    required: true
    description: The updated ad data
    schema:
      $ref: '#/definitions/Ad'
responses:
  200:
    description: The ad was updated successfully
  404:
    description: Ad not found
  400:
    description: The request was invalid
  500:
    description: An error occurred while updating the ad
    """

    update_data = request.json
    if not isinstance(update_data, dict):
        return jsonify({'error': 'Invalid update data'}), 400

    update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()

    try:
        result = ads_collection.update_one({'_id': ad_id}, {'$set': update_data})
        if result.matched_count:
            return jsonify({'message': 'Ad updated'}), 200
        return jsonify({'error': 'Ad not found'}), 404
    except Exception:
        return jsonify({'error': 'Failed to update ad'}), 500

# Delete ad
@ad_routes_blueprint.route('/ads/<ad_id>', methods=['DELETE'])
def delete_ad(ad_id):
    """
Delete an ad
---
parameters:
  - name: ad_id
    in: path
    type: string
    required: true
    description: The ID of the ad to delete
responses:
  200:
    description: The ad was deleted successfully
  404:
    description: Ad not found
  500:
    description: An error occurred while deleting the ad
    """

    try:
        result = ads_collection.delete_one({'_id': ad_id})
        if result.deleted_count:
            return jsonify({'message': 'Ad deleted'}), 200
        return jsonify({'error': 'Ad not found'}), 404
    except Exception:
        return jsonify({'error': 'Failed to delete ad'}), 500

# Get random ad for device (not previously appeared)
@ad_routes_blueprint.route('/ads/random', methods=['GET'])
def get_random_ad():
    """
Get a random ad for a device
---
parameters:
  - name: deviceId
    in: query
    type: string
    required: true
    description: Unique device identifier
responses:
  200:
    description: A random ad was returned successfully
  204:
    description: No ads available
  400:
    description: Missing deviceId parameter
  500:
    description: An error occurred while retrieving a random ad
    """
    device_id = request.args.get('deviceId')

    # Step 1: Validate device_id
    if not isinstance(device_id, str) or not device_id.strip():
        return jsonify({'error': 'Missing or invalid deviceId'}), 400

    device_id = device_id.strip()

    try:
        # Step 2: Get IDs of ads already seen by this device
        appeared_ad_ids_raw = events_collection.distinct('adId', {'deviceId': device_id})
        
        appeared_ad_ids = appeared_ad_ids_raw

        # Step 3: Get ads not yet shown
        unappeared_ads = list(ads_collection.find({'_id': {'$nin': appeared_ad_ids}}))

        # Step 4: Fallback – show any ad if none unappeared
        if not unappeared_ads:
            unappeared_ads = list(ads_collection.find())
            if not unappeared_ads:
                return jsonify({'message': 'No ads available'}), 204

        # Step 5: Choose and return random ad
        chosen_ad = random.choice(unappeared_ads)
        chosen_ad['_id'] = str(chosen_ad['_id'])
        return jsonify(chosen_ad), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve random ad'}), 500

# Send ad event (view, click, skip)
@ad_routes_blueprint.route('/ad_event', methods=['POST'])
def send_ad_event():
    """
    Log an ad event (view, click, skip)
    ---
    parameters:
      - name: event
        in: body
        required: true
        description: The event data
        schema:
          id: Event
          required:
            - adId
            - eventDetails
          properties:
            adId:
              type: string
              description: ID of the ad
            performerId:
              type: string
              description: ID of the performer associated with the ad (set automatically)
              readOnly: true
            eventDetails:
              type: object
              required:
                - appId
                - packageName
                - timestamp
                - deviceId
                - eventType
                - watchDuration
              properties:
                appId:
                  type: string
                packageName:
                  type: string
                timestamp:
                  type: string
                  format: date-time
                deviceId:
                  type: string
                eventType:
                  type: string
                  enum: [view, click, skip]
                watchDuration:
                  type: number
                  format: float
    responses:
      201:
        description: The event was logged successfully
      400:
        description: Invalid request
      500:
        description: Internal server error
    """
    data = request.json

    # Step 1: Validate top-level keys
    if 'adId' not in data or 'eventDetails' not in data:
        return jsonify({'error': 'Missing adId or eventDetails'}), 400

    ad_id = data['adId']
    event_details = data['eventDetails']

    # Step 2: Validate adId format
    if not isinstance(ad_id, str) or not ad_id.strip():
        return jsonify({'error': 'Invalid adId format'}), 400

    # Step 3: Validate eventDetails fields
    required_fields = ['appId', 'packageName', 'timestamp', 'deviceId', 'eventType', 'watchDuration']
    if not all(field in event_details for field in required_fields):
        return jsonify({'error': 'Missing eventDetails fields'}), 400

    # Step 4: Extract and normalize fields
    app_id = event_details['appId'].strip()
    package_name = event_details['packageName'].strip()
    timestamp = event_details['timestamp'].strip()
    device_id = event_details['deviceId'].strip()
    event_type = event_details['eventType'].strip().lower()
    watch_duration = event_details['watchDuration']

    # Step 5: Validate string fields are non-empty
    for field_name, value in {
        'appId': app_id, 'packageName': package_name,
        'timestamp': timestamp, 'deviceId': device_id, 'eventType': event_type
    }.items():
        if not isinstance(value, str) or not value:
            return jsonify({'error': f'Invalid or empty field: {field_name}'}), 400

    # Step 6: Validate eventType
    VALID_TYPES = {'view', 'click', 'skip'}
    if event_type not in VALID_TYPES:
        return jsonify({'error': 'Invalid eventType'}), 400

    # Step 7: Validate watchDuration
    try:
        watch_duration = float(watch_duration)
        if watch_duration < 0:
            return jsonify({'error': 'watchDuration must be non-negative'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid watchDuration format'}), 400
    
    ad_doc = ads_collection.find_one({'_id': ad_id})
    if not ad_doc:
      return jsonify({'error': 'Ad not found'}), 404

    performer_id = ad_doc.get('performerId')
    if not performer_id:
      return jsonify({'error': 'Ad has no performer assigned'}), 500

    # Step 8: Build event and insert
    event = {
        "adId": ad_id,
        "appId": app_id,
        "performerId": performer_id,
        "packageName": package_name,
        "timestamp": timestamp,
        "deviceId": device_id,
        "eventType": event_type,
        "watchDuration": watch_duration,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    try:
        events_collection.insert_one(event)
        return jsonify({'message': 'Event logged'}), 201
    except Exception:
        return jsonify({'error': 'Failed to store event'}), 500
    
# Get ad statistics by id
@ad_routes_blueprint.route('/ads/<ad_id>/stats', methods=['GET'])
def get_ad_statistics(ad_id):
    """
    Get statistics for an ad
    ---
    parameters:
      - name: ad_id
        in: path
        type: string
        required: true
        description: The ID of the ad to get statistics for
    responses:
      200:
        description: Ad statistics were returned successfully
        schema:
          type: object
          properties:
            packageName:
              type: string
              description: Package name of the application
            adId:
              type: string
              description: The ID of the ad
            adStats:
              type: object
              properties:
                views:
                  type: integer
                  description: Number of views
                clicks:
                  type: integer
                  description: Number of clicks
                skips:
                  type: integer
                  description: Number of skips
                avgWatchDuration:
                  type: number
                  format: float
                  description: Average watch duration in seconds
                clickThroughRate:
                  type: number
                  format: float
                  description: Click-through rate percentage
                conversionRate:
                  type: number
                  format: float
                  description: Conversion rate based on ad budget level
      404:
        description: Ad not found
      500:
        description: An error occurred while retrieving ad statistics
    """


    try:
        # Step 1: Fetch ad
        ad = ads_collection.find_one({'_id': ad_id})
        if not ad:
            return jsonify({'error': 'Ad not found'}), 404

        # Step 2: Fetch events
        view_events = list(events_collection.find({'adId': ad_id, 'eventType': 'view'}))
        click_events = list(events_collection.find({'adId': ad_id, 'eventType': 'click'}))
        skip_events = list(events_collection.find({'adId': ad_id, 'eventType': 'skip'}))

        # Step 3: Compute stats
        views = len(view_events)
        clicks = len(click_events)
        skips = len(skip_events)
        total_watch_duration = sum(event.get('watchDuration', 0) for event in view_events)
        avg_watch_duration = total_watch_duration / views if views > 0 else 0
        ctr = (clicks / views * 100) if views > 0 else 0

        # Step 4: Compute conversion rate
        BUDGET_LEVELS = {
            'low': 1,
            'medium': 2,
            'high': 3
        }
        budget_value = ad.get('adDetails', {}).get('budget', '').strip().lower()
        budget_level_score = BUDGET_LEVELS.get(budget_value, 1)
        conversion_rate = clicks / budget_level_score * 100

        # Step 5: Return JSON
        return jsonify({
            "packageNames": list(events_collection.distinct('packageName', {'adId': ad_id})),
            "adId": ad_id,
            "adStats": {
                "views": views,
                "clicks": clicks,
                "skips": skips,
                "avgWatchDuration": round(avg_watch_duration, 2),
                "clickThroughRate": round(ctr, 2),
                "conversionRate": round(conversion_rate, 2)
            }
        }), 200

    except Exception:
        return jsonify({'error': 'Failed to retrieve ad statistics'}), 500