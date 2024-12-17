import logging
import os
from flask import Flask, render_template, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Date, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pytz import timezone
from ddtrace import patch_all, tracer
from ddtrace.debugging import DynamicInstrumentation
from pythonjsonlogger import jsonlogger

# Read .env file and set variables in os.environ
def load_env_file(file_path=".env"):
    if os.path.exists(file_path):
        with open(file_path) as f:
            for line in f:
                # Skip comments and empty lines
                if line.startswith("#") or not line.strip():
                    continue
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

load_env_file()

service_name = os.environ.get("SERVICE", "default_service_name")

patch_all()
DynamicInstrumentation.enable()

logger = logging.getLogger(service_name)
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(status)s %(name)s %(message)s dd.trace_id %(dd.trace_id)s dd.span_id %(dd.span_id)s'
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

app = Flask(__name__, template_folder='templates')

DATABASE_URI = 'postgresql://username:password@db:5432/youtube_db'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    channel_id = Column(String)
    channel_name = Column(String)
    video_id = Column(String, unique=True)
    video_title = Column(String)
    video_url = Column(String)
    upload_date = Column(Date)
    duration = Column(Integer)

Base.metadata.create_all(engine)

@app.route('/', methods=['GET', 'POST'])
def dashboard():
    with tracer.trace("dashboard.route"):
        logger.info("Dashboard route accessed")
        session = Session()
        today_date = datetime.now(timezone('America/Mexico_City')).strftime('%Y-%m-%d')
        search_query = request.args.get('search_query', request.form.get('search_query', ''))
        start_date = request.args.get('start_date', request.form.get('start_date', ''))
        end_date = request.args.get('end_date', request.form.get('end_date', ''))

        query = session.query(Video.channel_name, func.count(Video.id).label('video_count')).group_by(Video.channel_name)
        if start_date and end_date:
            query = query.filter(Video.upload_date >= start_date, Video.upload_date <= end_date)
        if search_query:
            query = query.filter(Video.channel_name.ilike(f"%{search_query}%"))
        channel_counts = query.all()

        video_query = session.query(Video)
        if start_date and end_date:
            video_query = video_query.filter(Video.upload_date >= start_date, Video.upload_date <= end_date)
        if search_query:
            video_query = video_query.filter(Video.channel_name.ilike(f"%{search_query}%"))
        videos = video_query.all()

        logger.info("Dashboard data fetched", extra={"search_query": search_query, "start_date": start_date, "end_date": end_date})

        return render_template('dashboard_rendered.html', channel_counts=channel_counts, videos=videos, start_date=start_date, end_date=end_date, today_date=today_date, search_query=search_query)

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint accessed")
    return "OK", 200

@app.route('/api/videos', methods=['GET'])
def fetch_videos():
    with tracer.trace("fetch_videos.api"):
        logger.info("Fetch videos API endpoint accessed")

        session = Session()
        search_query = request.args.get('search_query', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')

        video_query = session.query(Video)
        if start_date and end_date:
            video_query = video_query.filter(Video.upload_date >= start_date, Video.upload_date <= end_date)
        if search_query:
            video_query = video_query.filter(Video.channel_name.ilike(f"%{search_query}%"))

        videos = video_query.all()

        video_data = [
            {
                "channel_name": video.channel_name,
                "video_title": video.video_title,
                "video_url": video.video_url,
                "upload_date": video.upload_date.strftime('%Y-%m-%d') if video.upload_date else None,
                "duration": video.duration,
            }
            for video in videos
        ]

        logger.info("Video data retrieved", extra={"count": len(video_data)})
        return jsonify(video_data)