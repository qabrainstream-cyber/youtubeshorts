from flask import Flask, request, jsonify
import requests
import isodate

app = Flask(__name__)

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

    def send_webhook(data):
        try:
            res = requests.post(webhook_url, json=data)
            print(f"✅ Webhook sent: {data['title']}")
        except Exception as e:
            print(f"❌ Webhook failed: {e}")

    # Main logic
    videos = get_recent_videos()
    for video in videos:
        video_id = video['id']['videoId']
        details = get_video_details(video_id)
        if not details:
            continue

        duration_iso = details['contentDetails']['duration']
        duration = isodate.parse_duration(duration_iso).total_seconds()

        if duration <= 60:
            snippet = details['snippet']
            data = {
                'videoId': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'publishedAt': snippet.get('publishedAt', ''),
                'url': f"https://youtube.com/shorts/{video_id}"
            }
            send_webhook(data)
            return jsonify({"status": "sent", "short_title": snippet.get('title', '')})

    return jsonify({"status": "no_short_found"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
