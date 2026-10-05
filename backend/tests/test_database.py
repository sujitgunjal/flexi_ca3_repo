from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database.database import (
    Base,
    _create_engine,
    initialize_database,
    test_connection as check_connection,
)
from app.database.models import RequestLog


def test_request_log_database_round_trip():
    test_engine = _create_engine("sqlite:///:memory:")
    try:
        assert check_connection(test_engine)
        initialize_database(test_engine)
        assert "request_logs" in inspect(test_engine).get_table_names()

        with Session(test_engine) as session:
            record = RequestLog(query="What is Docker?", complexity="simple")
            session.add(record)
            session.commit()
            record_id = record.id

        with Session(test_engine) as session:
            retrieved = session.get(RequestLog, record_id)
            assert retrieved is not None
            assert retrieved.query == "What is Docker?"
            assert retrieved.complexity == "simple"
            assert retrieved.selected_model is None
    finally:
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
