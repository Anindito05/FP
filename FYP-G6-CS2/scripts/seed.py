"""Create an initial admin user; no datasets or phone numbers are seeded."""
import argparse,asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.config import get_settings
from app.database import build_engine
from app.models import User
from app.security import hash_password

async def create_admin(email:str,password:str)->None:
    engine=build_engine(get_settings().database_url);factory=async_sessionmaker(engine,expire_on_commit=False)
    try:
        async with factory() as db:
            if await db.scalar(select(User).where(User.email==email.lower())): raise ValueError("Account already exists")
            db.add(User(email=email.lower(),password_hash=hash_password(password),display_name="Administrator",role="admin",is_guest=False,is_active=True));await db.commit()
    finally: await engine.dispose()
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--email",required=True);parser.add_argument("--password",required=True);args=parser.parse_args();asyncio.run(create_admin(args.email,args.password))
