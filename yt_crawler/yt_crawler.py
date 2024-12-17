import logging
import requests
from bs4 import BeautifulSoup
import datetime
from pytz import timezone
from sqlalchemy import create_engine, Column, Integer, String, Date, exc
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from ddtrace import tracer, patch_all
from pythonjsonlogger import jsonlogger

patch_all()

logger = logging.getLogger("yt_crawler")
logger.setLevel(logging.INFO)

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(status)s %(name)s %(message)s dd.trace_id %(dd.trace_id)s dd.span_id %(dd.span_id)s'
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

Base = declarative_base()

class YTVideo(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    channel_id = Column(String)
    channel_name = Column(String)
    video_id = Column(String, unique=True)
    video_title = Column(String)
    video_url = Column(String)
    upload_date = Column(Date)
    duration = Column(Integer)

DATABASE_URI = 'postgresql://username:password@db:5432/youtube_db'
engine = create_engine(DATABASE_URI)
Session = scoped_session(sessionmaker(bind=engine))

Base.metadata.create_all(engine)

def get_video_data(channel_id):
    with tracer.trace("yt_crawler.get_video_data"):
        logger.info(f"Fetching video data for channel {channel_id}")
        url = f'https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}'
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch data for channel {channel_id}: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'xml')
        channel_name = soup.find('title').text
        videos = []
        mexico_tz = timezone('America/Mexico_City')
        utc_tz = timezone('UTC')

        for entry in soup.find_all('entry'):
            published_date_utc = datetime.datetime.strptime(entry.published.text, '%Y-%m-%dT%H:%M:%S%z')
            published_date_mexico = published_date_utc.astimezone(mexico_tz)
            now = datetime.datetime.now(utc_tz)

            if (now - published_date_utc).days <= 60:
                video_id = entry.find('yt:videoId').text
                video_title = entry.title.text
                video_url = entry.link['href']
                duration_tag = entry.find('yt:duration')
                duration = int(duration_tag['seconds']) if duration_tag else None

                videos.append({
                    'channel_id': channel_id,
                    'channel_name': channel_name,
                    'video_id': video_id,
                    'video_title': video_title,
                    'video_url': video_url,
                    'upload_date': published_date_mexico.strftime('%Y-%m-%d'),
                    'duration': duration
                })

        logger.info(f"Fetched {len(videos)} videos for channel {channel_id}")
        return videos

def insert_videos(video_data):
    with tracer.trace("yt_crawler.insert_videos"):
        session = Session()
        for video in video_data:
            exists = session.query(YTVideo.video_id).filter_by(video_id=video['video_id']).scalar() is not None
            if not exists:
                yt_video = YTVideo(**video)
                session.add(yt_video)
                try:
                    session.commit()
                    logger.info(f"Inserted video {video['video_id']} into database")
                except exc.IntegrityError:
                    session.rollback()
                    logger.warning(f"Duplicate video found: {video['video_id']} - Skipping insertion.")

def run_crawler():
    with tracer.trace("yt_crawler.run_crawler"):
        logger.info("Starting YouTube Crawler")
        channel_ids = [
            'UCV_uXGmoHiPUW2kZYpVkbog', 'UCIY6Vn0rByu9okh5yYc0ZRg', 'UCCNgRIfWQKZyPkNvHEzPh7Q',
            'UCjQglRblUgJa2jshLaQSIjA', 'UCYO_jab_esuFRV4b17AJtAw', 'UCTUtqcDkzw7bisadh6AOx5w',
            'UCnkp4xDOwqqJD7sSM3xdUiQ', 'UCW6_2hUFm-jh3aToPvMZfJQ', 'UCvQECJukTDE2i6aCoMnS-Vg',
            'UC_SvYP0k05UKiJ_2ndB02IA', 'UCOmHUn--16B90oW2L6FRR3A', 'UC5slP3rsYf-4dpiPZvV6k5w',
            'UClGTZDyz3CSl92TgDqIr0nw', 'UCc5vZEM1MLUzCrg_aZIJdeA', 'UCMJecdKUslHToOEpeuRGwXg',
            'UCEOXxzW2vU0P-0THehuIIeg', 'UCMNMpSc81hvn5OC26yj-5Jw', 'UCfPpW6HcB_-tFgZ0DoulGzg',
            'UCr3cBLTYmIK9kY0F_OdFWFQ', 'UCuCk_7b2_4uSr6y5hFmjuMQ', 'UC2C_jShtL725hvbm1arSV9w',
            'UC4PIiYewI1YGyiZvgNlJNrA', 'UCAi_uNeDWRXj8C8yw358gWw', 'UCI5tGbwiVHy4BsZUXcSWvwQ',
            'UCVtL1edhT8qqY-j2JIndMzg', 'UCCYX4s1DCn51Hpf1peHS30Q', 'UCGc8ZVCsrR3dAuhvUbkbToQ',
            'UCLPMbl6z7UiLFTXNvoXShEg', 'UCl9StMQ79LtEvlrskzjoYbQ', 'UC0e3QhIYukixgh5VVpKHH9Q',
            'UCmA-0j6DRVQWo4skl8Otkiw', 'UC9-y-6csu5WGm29I7JiwpnA', 'UCsn6cjffsvyOZCZxvGoJxGg',
            'UCSpFnDQr88xCZ80N-X7t0nQ', 'UCz2iUx-Imr6HgDC3zAFpjOw', 'UCP7WmQ_U4GB3K51Od9QvM0w',
            'UCgFvT6pUq9HLOvKBYERzXSQ', 'UCMSsLqxqvZsNXi0Z-VjN89A', 'UCL6JmiMXKoXS6bpP1D3bk8g',
            'UCg0w_o_XPJnT-S1fva7NXyA', 'UCMtZt5KQmhCLXiQVRhIgzTg', 'UCYNbYGl89UUowy8oXkipC-Q',
            'UCq0EGvLTyy-LLT1oUSO_0FQ', 'UCUXqYwTCR6R3Wr-FkLTD4AQ', 'UCrUL8K81R4VBzm-KOYwrcxQ',
            'UCQMbqH7xJu5aTAPQ9y_U7WQ', 'UCgiwS5QQGJtOyRuuv52eqyQ', 'UCPD_bxCRGpmmeQcbe2kpPaA',
            'UCc9vRXCflu4zeRscej52pPA', 'UC8butISFwT-Wl7EV0hUK0BQ', 'UConJDkGk921yT9hISzFqpzw',
            'UC98tcedR6gULv8_b70WJKyw', 'UCFaSR7gUU39qJe-eDSiGY0A', 'UCePDFpCr78_qmVtpoB1Axaw',
            'UCFQMO-YL87u-6Rt8hIVsRjA', 'UCui-JiVE_8mHN24vjBoOHYQ', 'UCUNYSwNARexFwxXp3oPAtvg',
            'UCUuIQgNLG3xkqftlUtuFosw', 'UCsP7Bpw36J666Fct5M8u-ZA', 'UCVg2AVe6eTCTVoWQ9AwrIHg',
            'UCwO-UgquohXwoe7f0e6lMnw', 'UCbbQalJ4OaC0oQ0AqRaOJ9g', 'UCJW5UDaDqN66Iw1sbtXlEMA',
            'UCQ_jBtD8tlspQOOf4L1xPuw', 'UCgmC3e9qqK3FzqjzxGXHi_A', 'UCHn_K1zOBYZqtmIYkXLEIQw',
            'UCMmaBzfCCwZ2KqaBJjkj0fw', 'UCm22FAXZMw1BaWeFszZxUKw', 'UCsXVk37bltHxD1rDPwtNM8Q',
            'UCRFm-SX11evwoZjJ3rVv_HA', 'UCv8ZoZxvYcA3kEEl4Ct8J6w', 'UCpa-Zb0ZcQjTCPP1Dx_1M8Q',
            'UCqZQJ4600a9wIfMPbYc60OQ', 'UCSHZKyawb77ixDdsGog4iWA', 'UCOMrUmOTPD_AnSivjxptxpA',
            'UCY1kMZp36IQSyNx_9h4mpCg', 'UCgRBRE1DUP2w7HTH9j_L4OQ', 'UCR9sFzaG9Ia_kXJhfxtFMBA',
            'UCpZ5qUqpW4hW4zdfuBxMSJA', 'UCHnj59g7jezwTy5GeL8EA_g', 'UCbQ_WJsfwZvrSYHv6ywzyOA',
            'UCIOE_IzglfnHyaOYbvpJxjA', 'UCXjmz8dFzRJZrZY8eFiXNUQ', 'UC9x0AN7BWHpCDHSm9NiJFJQ',
            'UCoxcjq-8xIDTYp3uz647V5A', 'UCAPrhJwVweWZA8GEPoClSdw', 'UCKzJFdi57J53Vr_BkTfN3uQ',
            'UC-tLyAaPbRZiYrOJxAGB7dQ', 'UCR1IuLEqb6UEA_zQ81kwXfg', 'UC_I2tZMUZTs6z6przhH32hA',
            'UCP5tjEmvPItGyLhmjdwP7Ww', 'UCrYB2eCu6M_aKVLYcTb6JUg', 'UCcN3IuIAR6Fn74FWMQf6lFA',
            'UCkNRdK0q5KZssogiS--R4pQ', 'UC7BhHN8NyMMru2RUygnDXSg', 'UCxzC4EngIsMrPmbm6Nxvb-A',
            'UCDRmGMSgrtZkOsh_NQl4_xw', 'UCW6TXMZ5Pq6yL6_k5NZ2e0Q', 'UCEIwxahdLz7bap-VDs9h35A',
            'UCO6nDCimkF79NZRRb8YiDcA', 'UCj1VqrHhDte54oLgPG4xpuQ', 'UCT5C7yaO3RVuOgwP8JVAujQ',
            'UCAuUUnT6oDeKwE6v1NGQxug', 'UCsooa4yRKGN_zEE8iknghZA', 'UCk0fGHsCEzGig-rSzkfCjMw',
            'UC3sznuotAs2ohg_U__Jzj_Q', 'UCfdNM3NAhaBOXCafH7krzrA', 'UCYeF244yNGuFefuFKqxIAXw',
            'UCXgNowiGxwwnLeQ7DXTwXPg', 'UCxNlX8AUIh2nlLf4IL1DWzg', 'UCeYP27qLtfUMY1b1Cyy3WdQ',
            'UCRlICXvO4XR4HMeEB9JjDlA', 'UCBa659QWEk1AI4Tg--mrJ2A', 'UCZem9C5rWjSb0B8tV3k2EZg',
            'UCHnyfMqiRRG1u-2MsSQLbXA', 'UCLXo7UDZvByw2ixzpQCufnA', 'UCqmugCqELzhIMNYnsjScXXw',
            'UC6-ymYjG0SU0jUWnWh9ZzEQ', 'UC4EY_qnSeAP1xGsh61eOoJA', 'UCpCSAcbqs-sjEVfk_hMfY9w'
        ]
        for channel_id in channel_ids:
            video_data = get_video_data(channel_id)
            insert_videos(video_data)
        
        logger.info("YouTube Crawler run completed successfully.")

if __name__ == '__main__':
    run_crawler()
