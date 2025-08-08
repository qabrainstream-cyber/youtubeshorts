from flask import Flask, request, jsonify
import requests
import isodate
from datetime import datetime, timezone

app = Flask(__name__)

# Replace these with your actual values
API_KEY = 'AIzaSyBXv3F7SokEc3CEEN2w8y1NGFDDmcU7ALo'
CHANNEL_ID = 'UCpMfyR38-yRAKiHmtJNRoNA'

@app.route('/run', methods=['POST'])
def run_short_checker():
    webhook_url = request.json.get("webhook_url")

    def get_recent_videos():
        url = 'https://www.googleapis.com/youtube/v3/search'
        params = {
            'part': 'id',
            'channelId': CHANNEL_ID,
            'order': 'date',
            'maxResults': 10,
            'type': 'video',
            'key': API_KEY
        }
        response = requests.get(url, params=params)
        return response.json().get('items', [])

    def get_video_details(video_id):
        url = 'https://www.googleapis.com/youtube/v3/videos'
        params = {
            'part': 'snippet,contentDetails',
            'id': video_id,
            'key': API_KEY
        }
        response = requests.get(url, params=params)
        items = response.json().get('items', [])
        return items[0] if items else None

    def get_last_sent_video_id():
        if os.path.exists(LAST_SENT_FILE):
            with open(LAST_SENT_FILE, 'r') as f:
                return f.read().strip()
        return None

    def update_last_sent_video_id(video_id):
        with open(LAST_SENT_FILE, 'w') as f:
            f.write(video_id)

    def send_webhook(data):
        try:
            res = requests.post(webhook_url, json=data)
            print(f"✅ Webhook sent: {data['title']}")
        except Exception as e:
            print(f"❌ Webhook failed: {e}")

    last_sent_video_id = get_last_sent_video_id()
    videos = get_recent_videos()

    for video in videos:
        video_id = video['id']['videoId']
        if video_id == last_sent_video_id:
            print(f"🟡 Already sent today’s short: {video_id}")
            return jsonify({"status": "already_sent", "videoId": video_id})

        details = get_video_details(video_id)
        if not details:
            continue

        duration_iso = details['contentDetails']['duration']
        duration = isodate.parse_duration(duration_iso).total_seconds()

        if duration <= 60:
            snippet = details['snippet']
            published_at = snippet.get('publishedAt', '')

            try:
                published_dt = datetime.strptime(published_at, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)

                if published_dt.date() == now.date():
                    # It's a new short published today
                    data = {
                        'videoId': video_id,
                        'title': snippet.get('title', ''),
                        'description': snippet.get('description', ''),
                        'publishedAt': published_at,
                        'url': f"https://youtube.com/shorts/{video_id}"
                    }
                    send_webhook(data)
                    update_last_sent_video_id(video_id)
                    return jsonify({
                        "status": "sent",
                        "short_title": snippet.get('title', ''),
                        "url": f"https://youtube.com/shorts/{video_id}"
                        })
            except Exception as e:
                print(f"Date parsing error: {e}")
                continue

    return jsonify({"status": "no_new_short_today"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
