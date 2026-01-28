from app.db.session import engine, Base
import app.db.base  # noqa

Base.metadata.create_all(bind=engine)
