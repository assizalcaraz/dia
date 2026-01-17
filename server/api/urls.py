from django.urls import path

from . import views


urlpatterns = [
    path("sessions/", views.sessions, name="sessions"),
    path("sessions/current/", views.current_session, name="current_session"),
    path("events/recent/", views.events_recent, name="events_recent"),
    path("metrics/", views.metrics, name="metrics"),
]
