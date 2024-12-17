import os
from flask import Flask, render_template_string, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pytz import timezone
from ddtrace import patch_all
from flask.cli import with_appcontext
import click

patch_all()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@db:5432/youtube_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class YTVideo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    channel_id = db.Column(db.String(255))
    channel_name = db.Column(db.String(255))
    video_id = db.Column(db.String(255), unique=True)
    video_title = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    upload_date = db.Column(db.Date)
    duration = db.Column(db.Integer)

@click.command(name='create_tables')
@with_appcontext
def create_tables():
    db.create_all()

app.cli.add_command(create_tables)

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
<!--- Datadog RUM SDK --->
    <script>
      (function(h,o,u,n,d) {
        h=h[d]=h[d]||{q:[],onReady:function(c){h.q.push(c)}}
        d=o.createElement(u);d.async=1;d.src=n
        n=o.getElementsByTagName(u)[0];n.parentNode.insertBefore(d,n)
      })(window,document,'script','https://www.datadoghq-browser-agent.com/us1/v5/datadog-rum.js','DD_RUM')
      window.DD_RUM.onReady(function() {
        window.DD_RUM.init({
          clientToken: 'pub5733e110cbe54d9060b43329dc7ebb32',
          applicationId: '2ce13799-a82c-46dd-b365-7cbf795c2f62',
          site: 'datadoghq.com',
          service: 'yt_dashboard_test',
          env: 'yt_test_1',
          sessionSampleRate: 100,
          sessionReplaySampleRate: 20,
          trackUserInteractions: true,
          trackResources: true,
          trackLongTasks: true,
          defaultPrivacyLevel: 'mask-user-input',
        });
      })
    </script>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
            color: #333;
            margin: 0;
            padding: 0;
        }
        h1 {
            background-color: #282c34;
            color: #61dafb;
            padding: 20px;
            margin: 0;
            text-align: center;
        }
        form {
            background-color: #fff;
            padding: 20px;
            border-radius: 5px;
            margin: 20px;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        table {
            width: 90%;
            margin: 20px auto;
            border-collapse: collapse;
            background-color: #fff;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0,0,0,0.15);
        }
        table th, table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        table th {
            background-color: #f4f4f4;
        }
        table tr:hover {
            background-color: #f1f1f1;
        }
        button {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background-color: #282c34;
            color: #61dafb;
            cursor: pointer;
        }
        button:hover {
            background-color: #333;
        }
    </style>
    <script>
        function setTodayFilter() {
            var today = new Date('{{ today_date }}T00:00:00');
            document.getElementById('start_date').value = today.toISOString().split('T')[0];
            document.getElementById('end_date').value = today.toISOString().split('T')[0];
            document.forms[0].submit();
        }

        function showVideos(channelName, startDate, endDate) {
            window.location.href = '/?channel_name_filter=' + encodeURIComponent(channelName) + 
                                   '&start_date=' + encodeURIComponent(startDate) + 
                                   '&end_date=' + encodeURIComponent(endDate);
        }

        function toggleVideos() {
            var videoTable = document.getElementById('video-table');
            videoTable.style.display = videoTable.style.display === 'none' ? 'table' : 'none';
        }
    </script>
</head>
<body>
    <h1>My YouTube Dashboard</h1>

    <form method="POST">
        <label for="start_date">Start Date:</label>
        <input type="date" id="start_date" name="start_date" {% if start_date %}value="{{ start_date }}"{% endif %}>
        <label for="end_date">End Date:</label>
        <input type="date" id="end_date" name="end_date" {% if end_date %}value="{{ end_date }}"{% endif %}>
        <label for="search_query">Search:</label>
        <input type="text" id="search_query" name="search_query" {% if search_query %}value="{{ search_query }}"{% endif %}>
        <button type="submit">Filter</button>
        <button type="button" onclick="setTodayFilter()">Today's Videos</button>
        <input type="hidden" id="channel_name_filter" name="channel_name_filter">
        <button type="button" onclick="window.location.href='/'">Restart App</button>
    </form>

    <table border="1">
        <thead>
            <tr>
                <th>Channel Name</th>
                <th>Video Count</th>
            </tr>
        </thead>
        <tbody>
            {% for row in channel_counts %}
                <tr>
                    <td><a href="#" onclick="showVideos('{{ row['Channel Name'] }}', '{{ start_date }}', '{{ end_date }}')">{{ row['Channel Name'] }}</a></td>
                    <td>{{ row['Video Count'] }}</td>
                </tr>
            {% endfor %}
        </tbody>
    </table>

    <button onclick="toggleVideos()">Toggle Videos</button>

    <table border="1" id="video-table" style="display:none;">
        <thead>
            <tr>
                <th>Channel Name</th>
                <th>Video Title</th>
                <th>Upload Date</th>
                <th>Thumbnail</th>
            </tr>
        </thead>
        <tbody>
            {% for row in videos %}
                <tr>
                    <td>{{ row['Channel Name'] }}</td>
                    <td><a href="{{ row['Video URL'] }}" target="_blank">{{ row['Video Title'] }}</a></td>
                    <td>{{ row['Upload Date'] }}</td>
                    <td><img src="https://img.youtube.com/vi/{{ row['Video ID'] }}/default.jpg" alt="{{ row['Video Title'] }}"></td>
                </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    mexico = timezone('America/Mexico_City')
    today_date = datetime.now(mexico).strftime('%Y-%m-%d')

    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        channel_name_filter = request.form.get('channel_name_filter')
        search_query = request.form.get('search_query')
    else:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        channel_name_filter = request.args.get('channel_name_filter')
        search_query = request.args.get('search_query')

    query = YTVideo.query

    if start_date and start_date != 'None' and end_date and end_date != 'None':
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        query = query.filter(YTVideo.upload_date.between(start_date, end_date))

    if channel_name_filter:
        query = query.filter_by(channel_name=channel_name_filter)

    if search_query:
        query = query.filter(YTVideo.channel_name.ilike(f'%{search_query}%'))

    filtered_videos = query.all()
    channel_counts = db.session.query(YTVideo.channel_name, db.func.count(YTVideo.video_id)).group_by(YTVideo.channel_name).all()

    return render_template_string(HTML_TEMPLATE, 
                                  channel_counts=[{'Channel Name': row[0], 'Video Count': row[1]} for row in channel_counts],
                                  videos=[{
                                    'Channel Name': video.channel_name,
                                    'Video Title': video.video_title,
                                    'Upload Date': video.upload_date,
                                    'Video URL': video.video_url,
                                    'Video ID': video.video_id
                                  } for video in filtered_videos],
                                  start_date=start_date if start_date not in [None, 'None'] else None,
                                  end_date=end_date if end_date not in [None, 'None'] else None,
                                  today_date=today_date,
                                  search_query=search_query)

if __name__ == '__main__':
    app.run(port=5010, host='0.0.0.0')