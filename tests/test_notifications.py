"""
tests/test_notifications.py — Mixtape

Tests for notification creation logic.
"""

import pytest
from app import create_app, db
from models import User, Song
from services.notification_service import rate_song, get_notifications


@pytest.fixture
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


def test_rating_creates_notification_for_song_sharer(app):
    """Rating a friend's shared song should create a notification for the sharer."""
    with app.app_context():
        sharer = User(username="sharer", email="sharer@example.com")
        rater = User(username="listener", email="listener@example.com")
        db.session.add_all([sharer, rater])
        db.session.flush()

        song = Song(title="Cool Song", artist="Artist", shared_by=sharer.id)
        db.session.add(song)
        db.session.commit()

        rate_song(rater.id, song.id, 5)

        notifications = get_notifications(sharer.id)
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification["type"] == "song_rated"
        assert "listener rated your song 'Cool Song'" in notification["body"]


def test_rating_own_song_does_not_create_notification(app):
    """A user rating their own shared song should not notify themselves."""
    with app.app_context():
        sharer = User(username="sharer", email="sharer@example.com")
        db.session.add(sharer)
        db.session.flush()

        song = Song(title="Cool Song", artist="Artist", shared_by=sharer.id)
        db.session.add(song)
        db.session.commit()

        rate_song(sharer.id, song.id, 5)

        notifications = get_notifications(sharer.id)
        assert notifications == []
