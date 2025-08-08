from flask import Flask, request, jsonify, make_response
import requests
import isodate
from datetime import datetime, timezone

app = Flask(__name__)

# Your API key and channel ID
API_KEY = 'AIzaSyBXv3F7SokEc3CEEN2w8y1NGFDDmcU7ALo'
CHANNEL_ID = 'UCpMfyR38-yRAKiHmtJNRoNA'

@app.route('/run', methods=['POST'])
def run_short_checker():
    webhook_url = request.json.get("webhook_url")
    target_date_str = request.json.get("date")

    if not webhook_url or not target_date_str:
        return make_response(jsonify({
            "status": "error",
            "message": "Missing webhook_url or date"
        }), 400)

    try:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except ValueError:
        return make_response(jsonify({
            "status": "error",
            "message": "Invalid date format. Use YYYY-MM-DD"
        }), 400)

    # Get latest videos
    search_url = 'https://www.googleapis.com/youtube/v3/search'
    search_params = {
        'part': 'id',
        'channelId': CHANNEL_ID,
        'order': 'date',
        'maxResults': 10,
        'type': 'video',
        'key': API_KEY
    }
    search_res = requests.get(search_url, params=search_params).json()
    video_items = search_res.get('items', [])

    for item in video_items:
        video_id = item['id']['videoId']

        # Get video details
        details_url = 'https://www.googleapis.com/youtube/v3/videos'
        details_params = {
            'part': 'snippet,contentDetails',
            'id': video_id,
            'key': API_KEY
        }
        details_res = requests.get(details_url, params=details_params).json()
        items = details_res.get('items', [])
        if not items:
            continue

        video = items[0]
        snippet = video['snippet']
        content = video['contentDetails']
        published_at = snippet.get('publishedAt', '')

        try:
            published_dt = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        except Exception as e:
            continue

        # Check if it's a short published on the target date
        duration = isodate.parse_duration(content['duration']).total_seconds()
        if duration <= 60 and published_dt.date() == target_date:
            short_url = f"https://youtube.com/shorts/{video_id}"
            title = snippet.get('title', '')

            # Send to webhook
            try:
                requests.post(webhook_url, json={
                    "title": title,
                    "url": short_url
                })
            except:
                pass

            # Return response to Make
            response = make_response(jsonify({
                "status": "sent",
                "title": title,
                "url": short_url
            }))
            response.headers["Content-Type"] = "application/json"
            response.headers["Content-Encoding"] = "identity"
            return response

    # No match found
    response = make_response(jsonify({
        "status": "no_short_found",
        "date": target_date_str
    }))
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Encoding"] = "identity"
    return response

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
