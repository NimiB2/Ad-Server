from flask import request, jsonify, Blueprint
from mongo_db_connection_manager import MongoConnectionManager
import random
from datetime import datetime, timezone
from email_validator import validate_email, EmailNotValidError
import uuid
import re


ad_routes_blueprint = Blueprint('ads', __name__)

db = MongoConnectionManager.get_db()
ads_collection = db['ads']
performers_collection = db['performers']
daily_stats_collection = db['daily_ad_stats']
events_by_day_collection = db['events_by_day']
developers_collection = db['developers']

try:
    # Index for performer stats queries
    daily_stats_collection.create_index(
        [("performerId", 1), ("date", 1)],
        name="performer_date_idx"
    )
    
    # Index for ad stats queries
    daily_stats_collection.create_index(
        [("adId", 1), ("date", 1)],
        name="ad_date_idx"
    )
except Exception as e:
    print(f"[Init] Index creation failed: {e}")

# Helper functions
def apply_date_filter(match_dict, args):
    """Apply date filtering based on query parameters"""
    date_from = args.get('from')
    date_to = args.get('to')
    
    if date_from or date_to:
        match_dict['date'] = {}
        if date_from:
            match_dict['date']['$gte'] = date_from
        if date_to:
            match_dict['date']['$lte'] = date_to

def build_stats_pipeline(match_criteria):
    """Build a standard stats aggregation pipeline"""
    return [
        {'$match': match_criteria},
        {'$group': {
            '_id': '$adId',
            'views': {'$sum': '$counts.view'},
            'clicks': {'$sum': '$counts.click'},
            'skips': {'$sum': '$counts.skip'},
            'exits': {'$sum': '$counts.exit'},
            'watchDurationSum': {'$sum': '$watchDurationSum'}
        }}
    ]

def validate_email_format(email):
    """
    Validate if a string is a properly formatted email address
    
    Args:
        email (str): The email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    email = email.strip()
    if not email:
        return False
    
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_regex, email))

def calculate_ad_stats(stats_data, budget=None):
    """
    Calculate ad statistics from raw aggregation data
    
    Args:
        stats_data (dict): Raw aggregation data with views, clicks, etc.
        budget (str, optional): Budget level for conversion rate calculation
        
    Returns:
        dict: Calculated statistics
    """
    views = stats_data.get('views', 0)
    clicks = stats_data.get('clicks', 0)
    skips = stats_data.get('skips', 0)
    watch_sum = stats_data.get('watchDurationSum', 0)
    
    # Calculate derived metrics
    avg_watch = watch_sum / views if views else 0
    ctr = (clicks / views * 100) if views else 0
    
    stats = {
        "views": views,
        "clicks": clicks,
        "skips": skips,
        "avgWatchDuration": round(avg_watch, 2),
        "clickThroughRate": round(ctr, 2)
    }
    
    # Add conversion rate if budget is provided
    if budget:
        BUDGET_LEVELS = {'low': 1, 'medium': 2, 'high': 3}
        budget_level = budget.strip().lower() if isinstance(budget, str) else ''
        conv_rate = (clicks / BUDGET_LEVELS.get(budget_level, 1) * 100) if views else 0
        stats["conversionRate"] = round(conv_rate, 2)
    
    return stats

# Create performer
@ad_routes_blueprint.route('/performers', methods=['POST'])
def create_performer():
    """
    Create a new performer or return existing performer by email
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
              description: The performer's name
            email:
              type: string
              format: email
              description: The performer's email (must be unique and properly formatted)
        examples:
          application/json:
            {
              "name": "John Smith",
              "email": "john.smith@example.com"
            }
    responses:
      201:
        description: Performer created successfully
        schema:
          properties:
            message:
              type: string
              example: "Performer created"
            performerId:
              type: string
              example: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
      200:
        description: Performer already exists, returned existing ID
        schema:
          properties:
            message:
              type: string
              example: "Performer already exists"
            performerId:
              type: string
              example: "f47ac10b-58cc-4372-a567-0e02b2c3d479"
      400:
        description: Invalid input or email format
        schema:
          properties:
            error:
              type: string
              example: "Invalid email format"
      500:
        description: Internal server error
        schema:
          properties:
            error:
              type: string
              example: "Failed to create performer"
    """
    data = request.json
    required_fields = ['name', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing name or email'}), 400

    name = data['name'].strip()
    email = data['email'].strip()
    if not name or not email:
        return jsonify({'error': 'Name and email cannot be empty'}), 400
    
    if not validate_email_format(email):
        return jsonify({'error': 'Invalid email format'}), 400

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
        return jsonify({'error': f'Failed to create performer: {str(e)}'}), 500

# check if performer exists by email
@ad_routes_blueprint.route('/performers/check-email', methods=['POST'])
def check_performer_email():
    """
    Check if a performer exists with the given email
    ---
    parameters:
      - name: email_data
        in: body
        required: true
        description: The email to check
        schema:
          properties:
            email:
              type: string
              format: email
              description: The performer's email
    responses:
      200:
        description: Email exists
        schema:
          properties:
            exists:
              type: boolean
              example: true
      400:
        description: Invalid input or email format
    """
    data = request.json
    if 'email' not in data or not data['email'].strip():
        return jsonify({'error': 'Missing or empty email'}), 400
    
    email = data['email'].strip()
    
    if not validate_email_format(email):
      return jsonify({'error': 'Invalid email format'}), 400

    # Check if email exists
    existing = performers_collection.find_one({'email': email})
    if existing:
        return jsonify({'exists': True, 'performerId': existing['_id']}), 200
    else:
        return jsonify({'exists': False}), 200

# Get all performers (for admin/developer view)
@ad_routes_blueprint.route('/performers', methods=['GET'])
def get_all_performers():
    """
    Get all performers (admin/developer only)
    ---
    responses:
      200:
        description: A list of all performers was returned successfully
      500:
        description: An error occurred while retrieving performers
    """
    try:
        performers = list(performers_collection.find())
        for performer in performers:
            performer['_id'] = str(performer['_id'])
        return jsonify(performers), 200
    except Exception:
        return jsonify({'error': 'Failed to retrieve performers'}), 500

# Login developer
@ad_routes_blueprint.route('/developers/login', methods=['POST'])
def developer_login():
    """
    Developer Login
    ---
    tags:
      - developers
    parameters:
      - name: credentials
        in: body
        required: true
        description: Developer email for login
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              format: email
              description: Developer's email
    responses:
      200:
        description: Developer found and login successful
        schema:
          properties:
            exists:
              type: boolean
              example: true
            developerId:
              type: string
              example: "dev-uuid-1"
      404:
        description: Developer not found
        schema:
          properties:
            exists:
              type: boolean
              example: false
      400:
        description: Invalid request
        schema:
          properties:
            error:
              type: string
              example: "Missing email"
    """
    data = request.json
    if 'email' not in data:
        return jsonify({'error': 'Missing email'}), 400
    
    email = data['email'].strip()

    if not validate_email_format(email):
      return jsonify({'error': 'Invalid email format'}), 400
    
    # Check if developer exists
    developer = developers_collection.find_one({'email': email})
    if developer:
        return jsonify({
            'exists': True, 
            'developerId': developer['_id']
        }), 200
    else:
        return jsonify({'exists': False}), 404

# Create a developer
@ad_routes_blueprint.route('/developers', methods=['POST'])
def create_developer():
    """
    Create a new developer
    ---
    tags:
      - developers
    parameters:
      - name: developer
        in: body
        required: true
        description: The developer to create
        schema:
          type: object
          required:
            - name
            - email
          properties:
            name:
              type: string
              description: The developer's name
            email:
              type: string
              format: email
              description: The developer's email (must be unique)
    responses:
      201:
        description: Developer created successfully
        schema:
          properties:
            message:
              type: string
              example: "Developer created"
            developerId:
              type: string
              example: "dev-uuid-1"
      200:
        description: Developer already exists
        schema:
          properties:
            message:
              type: string
              example: "Developer already exists"
            developerId:
              type: string
              example: "dev-uuid-1"
      400:
        description: Invalid input or email format
        schema:
          properties:
            error:
              type: string
              example: "Invalid email format"
      500:
        description: Internal server error
        schema:
          properties:
            error:
              type: string
              example: "Failed to create developer"
    """
    data = request.json
    required_fields = ['name', 'email']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing name or email'}), 400

    name = data['name'].strip()
    email = data['email'].strip()
    if not name or not email:
        return jsonify({'error': 'Name and email cannot be empty'}), 400
    
    if not validate_email_format(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Check if email exists
    existing = developers_collection.find_one({'email': email})
    if existing:
        return jsonify({
            'message': 'Developer already exists',
            'developerId': existing['_id']
        }), 200

    developer = {
        "_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }

    try:
        developers_collection.insert_one(developer)
        return jsonify({'message': 'Developer created', 'developerId': developer['_id']}), 201
    except Exception as e:
        return jsonify({'error': f'Failed to create developer: {str(e)}'}), 500

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
            - performerEmail
          properties:
            adName:
              type: string
              description: The name of the ad
            performerEmail:
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
        examples:
          application/json:
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

    required_fields = ['adName', 'performerEmail', 'adDetails']
    if not all(field in ad_data for field in required_fields):
        return jsonify({'error': 'Missing required fields (adName, performerEmail, adDetails)'}), 400

    performer_email = ad_data['performerEmail'].strip()
    performer = performers_collection.find_one({'email': performer_email})
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
        "performerName": performer["name"],
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
    except Exception:
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
    except Exception:
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
        # 1. First find the ad to get performer ID
        ad = ads_collection.find_one({'_id': ad_id})
        if not ad:
            return jsonify({'error': 'Ad not found'}), 404
            
        performer_id = ad.get('performerId')
        
        # 2. Delete ad from ads collection
        ads_collection.delete_one({'_id': ad_id})
        
        # 3. Remove ad from performer's ads array
        performers_collection.update_one(
            {'_id': performer_id},
            {'$pull': {'ads': ad_id}}
        )
        
        # 4. Clean up events that reference this ad
        # (Optional) Filter by date for performance on large collections
        events_by_day_collection.update_many(
            {},
            {'$pull': {'events': {'adId': ad_id}}}
        )
        
        # 5. Remove statistics for this ad
        daily_stats_collection.delete_many({'adId': ad_id})
        
        return jsonify({'message': 'Ad and related data deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to delete ad: {str(e)}'}), 500
        
# Get random ad for app
@ad_routes_blueprint.route('/ads/random', methods=['GET'])
def get_random_ad():
    """
    Get a random ad for an app
    ---
    parameters:
      - name: packageName
        in: query
        type: string
        required: true
        description: Package name of the app
    responses:
      200:
        description: A random ad was returned successfully
      204:
        description: No ads available
      400:
        description: Missing packageName parameter
      500:
        description: An error occurred while retrieving a random ad
    """

    package_name = request.args.get('packageName')
    if not isinstance(package_name, str) or not package_name.strip():
        return jsonify({'error': 'Missing or invalid packageName'}), 400
    package_name = package_name.strip() 

    try:
        all_ads = list(ads_collection.find())
        
        if not all_ads:
            return jsonify({'message': 'No ads available'}), 204

        chosen_ad = random.choice(all_ads)
        chosen_ad['_id'] = str(chosen_ad['_id'])
        return jsonify(chosen_ad), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve random ad: {str(e)}'}), 500

# Send ad event
@ad_routes_blueprint.route('/ad_event', methods=['POST'])
def send_ad_event():
    """
    Log an ad event (view, click, skip, exit)
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
            - timestamp
            - eventDetails
          properties:
            adId:
              type: string
            timestamp:
              type: string
              format: date-time
            eventDetails:
              type: object
              required:
                - packageName
                - eventType
                - watchDuration
              properties:
                packageName:
                  type: string
                eventType:
                  type: string
                  enum: [view, click, skip, exit]
                watchDuration:
                  type: number
                  format: float
    notes:
      - Each event also updates a daily summary doc in **daily_ad_stats**
        (write-time counter).
    responses:
      201:
        description: The event was logged successfully
      400:
        description: Invalid request
      404:
        description: Ad not found
      500:
        description: Internal server error
    """
    data = request.json

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

    for field_name, value in {
        'packageName': package_name,
        'eventType': event_type,
        'timestamp': timestamp
    }.items():
        if not isinstance(value, str) or not value:
            return jsonify({'error': f'Invalid or empty field: {field_name}'}), 400

    VALID_TYPES = {'view', 'click', 'skip', 'exit'}
    if event_type not in VALID_TYPES:
        return jsonify({'error': 'Invalid eventType'}), 400

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

    try:
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
        
        # Update daily performer stats
        stats_key = {
            "performerId": performer_id,
            "date": today_date
        }
        
        inc_fields = {f"counts.{event_type}": 1}
        
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
        
        return jsonify({'message': 'Event logged'}), 201

    except Exception as e:
        return jsonify({'error': f'Failed to store event: {str(e)}'}), 500

# Get ad statistics by id
@ad_routes_blueprint.route('/ads/<ad_id>/stats', methods=['GET'])
def get_ad_statistics(ad_id):
    
    """
    Get aggregated statistics for an ad

    ---
    parameters:
      - name: ad_id
        in: path
        type: string
        required: true
        description: ID of the ad whose statistics are requested
      - name: from
        in: query
        type: string
        required: false
        format: date
        description: (Optional) Inclusive start date — ISO-8601 YYYY-MM-DD
      - name: to
        in: query
        type: string
        required: false
        format: date
        description: (Optional) Inclusive end date — ISO-8601 YYYY-MM-DD
    responses:
      200:
        description: Statistics calculated from daily roll-ups
      404:
        description: Ad not found
      500:
        description: Server error
    tags:
      - Ads
    """

    ad_doc = ads_collection.find_one({'_id': ad_id})
    if not ad_doc:
        return jsonify({'error': 'Ad not found'}), 404

    match = {'adId': ad_id}
    apply_date_filter(match, request.args)

    pipeline = build_stats_pipeline(match)
    agg = list(daily_stats_collection.aggregate(pipeline))
    
    totals = agg[0] if agg else {
        'views': 0, 'clicks': 0, 'skips': 0, 'exits': 0, 'watchDurationSum': 0
    }

    budget = ad_doc.get('adDetails', {}).get('budget', '')
    stats = calculate_ad_stats(totals, budget)

    return jsonify({
        'adId': ad_id,
        'dateRange': {'from': request.args.get('from'), 'to': request.args.get('to')},
        'adStats': stats
    }), 200

# Get ad statistics by performer
@ad_routes_blueprint.route('/performers/<performer_id>/stats', methods=['GET'])
def get_performer_statistics(performer_id):
    """
    Get statistics for all ads of a performer
    ---
    parameters:
      - name: performer_id
        in: path
        type: string
        required: true
      - name: from
        in: query
        type: string
        required: false
        format: date
        description: (Optional) Inclusive start date — ISO-8601 YYYY-MM-DD
      - name: to
        in: query
        type: string
        required: false
        format: date
        description: (Optional) Inclusive end date — ISO-8601 YYYY-MM-DD
    responses:
      200:
        description: Performer ad statistics returned successfully
      404:
        description: Performer not found
      500:
        description: Server error
    """
    try:
        performer = performers_collection.find_one({'_id': performer_id})
        if not performer:
            return jsonify({'error': 'Performer not found'}), 404

        ad_ids = performer.get('ads', [])
        stats_list = []

        match = {'performerId': performer_id}
        apply_date_filter(match, request.args)

        # Use helper function to build the pipeline
        pipeline = build_stats_pipeline(match)
        ad_stats = {stat['_id']: stat for stat in daily_stats_collection.aggregate(pipeline) if stat['_id'] in ad_ids}

        
        for ad_id in ad_ids:
            stats = ad_stats.get(ad_id, {
                'views': 0, 'clicks': 0, 'skips': 0, 'exits': 0, 'watchDurationSum': 0
            })
            
            ad_stats_result = calculate_ad_stats(stats)
            ad_stats_result["adId"] = ad_id
            ad_stats_result["exits"] = stats.get('exits', 0) 
            stats_list.append(ad_stats_result)


        return jsonify({
            "performerId": performer_id,
            "adsStats": stats_list
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to retrieve performer statistics: {str(e)}'}), 500