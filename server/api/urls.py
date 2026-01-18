from django.urls import path

from . import views


urlpatterns = [
    path("sessions/", views.sessions, name="sessions"),
    path("sessions/current/", views.current_session, name="current_session"),
    path("events/recent/", views.events_recent, name="events_recent"),
    path("metrics/", views.metrics, name="metrics"),
    path("summaries/", views.daily_summaries, name="daily_summaries"),
    path("summaries/latest/", views.summaries_latest, name="summaries_latest"),
    path("summaries/<str:day_id>/list/", views.summaries_list, name="summaries_list"),
    path("summaries/<str:day_id>/<str:summary_id>/content/", views.summary_content, name="summary_content"),
    path("docs/list/", views.docs_list, name="docs_list"),
    path("docs/<path:doc_path>/", views.doc_content, name="doc_content"),
    path("day/closed/", views.day_closed, name="day_closed"),
    path("day/today/", views.day_today, name="day_today"),
    path("jornada/<str:day_id>/", views.jornada, name="jornada"),
    path("jornada/<str:day_id>/human/", views.jornada_human_update, name="jornada_human_update"),
    path("notes/tmp/<str:day_id>/", views.notes_tmp_list, name="notes_tmp_list"),
    path("notes/tmp/<str:day_id>/<str:file_name>", views.notes_tmp_content, name="notes_tmp_content"),
    path("captures/recent/", views.captures_recent, name="captures_recent"),
    path("captures/errors/open/", views.errors_open, name="errors_open"),
    path("chain/latest/", views.chain_latest, name="chain_latest"),
    path("endpoints.md", views.endpoints_doc, name="endpoints_doc"),
]
