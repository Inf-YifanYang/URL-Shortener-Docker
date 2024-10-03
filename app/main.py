import secrets
import datetime
from .config import get_settings

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from . import schemas
from .database import init_db, get_db, URLMapping, SessionLocal
from .utils import *

app = FastAPI()
init_db()

@app.get("/")
def read_root():
    s = ['Welcome to the URL shortener API',
        'Endpoint (root): /',
        'Endpoint (create shortened URL): /service',
        'Endpoint (forward to long URL): /{url_short}'
        'Endpoint (obtain information for shortened URI): /info/{url_short}'
    ]
    s = (' '*10).join(s)
    return s

"""
Creating A Shortened URL
"""
@app.post("/service", response_model=schemas.CreationResponse)
def create_url(request: schemas.CreationRequest, db: Session = Depends(get_db)):

    # creation time & expiration time
    creation_time = datetime.datetime.now(datetime.UTC)
    expiration_time = creation_time + datetime.timedelta(minutes=request.expiration_minutes)
    
    # generate short url
    short_url_size = get_settings().SHORTEN_URL_SIZE
    short_url = create_random_key(short_url_size)
    while db.query(URLMapping).filter_by(short_url=short_url, is_active=True).first():
        short_url = create_random_key(short_url_size)

    # create instance to save in database
    db_url_mapping = URLMapping(
        long_url=request.long_url, 
        short_url=short_url, 
        creation_time=creation_time,
        expiration_time=expiration_time,
        is_active=True
    )

    # update database
    db.add(db_url_mapping)
    db.commit()
    db.refresh(db_url_mapping)

    # generate response
    response = schemas.CreationResponse(
                    long_url=db_url_mapping.long_url,
                    expiration_minutes=request.expiration_minutes,
                    expiration_time=db_url_mapping.expiration_time,
                    creation_time=db_url_mapping.creation_time,
                    short_url=db_url_mapping.short_url,
                    is_active=db_url_mapping.is_active
                )
    return response

"""
Forward Shortened URL to Original Long URL
"""
@app.get("/{short_url}")
def forward_to_target_url(short_url: str,
                          request: Request,
                          db: Session = Depends(get_db)):
    
    db_url_mapping = db.query(URLMapping).filter_by(short_url=short_url).first()
    if db_url_mapping:
        current_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        expiration_time = db_url_mapping.expiration_time

        if current_time > expiration_time:
            # link expired
            raise_expired_error(request)
        else:
            return RedirectResponse(db_url_mapping.long_url)
    else:
        raise_not_found_error(request)

"""
Retrieve Shortened URL Info
"""
@app.get("/info/{short_url}")
def get_url_info(short_url: str, 
                 request: Request, 
                 db: Session = Depends(get_db)):
    db_url_mapping = db.query(URLMapping).filter_by(short_url=short_url).first()
    if db_url_mapping:
        current_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        expiration_time = db_url_mapping.expiration_time
        if current_time > expiration_time:
            remaining_time = '00:00:00'
        else:
            remaining_time = expiration_time - current_time
            remaining_time = format_timedelta(remaining_time)

        response = schemas.InfoResponse(
                    long_url=db_url_mapping.long_url,
                    expiration_time=db_url_mapping.expiration_time,
                    creation_time=db_url_mapping.creation_time,
                    short_url=db_url_mapping.short_url,
                    remaining_time=remaining_time,
                    is_active=db_url_mapping.is_active,
                    )
        return response  
    else:
        raise_not_found_error(request)


""" 
deactivate expired URLs in the database periodically
"""
def deactivate_expired_urls():
    db = SessionLocal()
    current_time = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    expired_url_mappings = db.query(URLMapping).filter(URLMapping.expiration_time < current_time, 
                                                       URLMapping.is_active == True).all()

    if expired_url_mappings:
        for db_url_mapping in expired_url_mappings:
            db_url_mapping.is_active = False
        db.commit()
        print(f"Deactivate {len(expired_url_mappings)} expired URLs in the database.")
    db.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(deactivate_expired_urls, 'interval', minutes=1)  # scan every minutes, can be set to large number
    scheduler.start()

@app.on_event("startup")
def startup_event():
    start_scheduler()