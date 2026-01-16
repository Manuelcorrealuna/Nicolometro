import os
from supabase import create_client
import streamlit as st

_client = None


def _get_secret(key, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key, default)


def get_client():
    global _client
    if _client is not None:
        return _client

    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_ANON_KEY en secrets.")

    _client = create_client(url, key)
    return _client


def is_admin_mode():
    value = _get_secret("ADMIN_MODE", "false")
    return str(value).lower() in ("1", "true", "yes", "on")


def _raise_for_error(response):
    if hasattr(response, "error") and response.error:
        message = getattr(response.error, "message", None) or str(response.error)
        raise RuntimeError(message)


def get_people():
    client = get_client()
    response = client.table("people").select("*").order("display_name").execute()
    _raise_for_error(response)
    return response.data or []


def add_person(display_name, alias=None):
    client = get_client()
    payload = {"display_name": display_name}
    if alias:
        payload["alias"] = alias
    response = client.table("people").insert(payload).execute()
    _raise_for_error(response)
    return response.data


def get_categories(active_only=True, kind=None):
    client = get_client()
    query = client.table("categories").select("*").order("points", desc=True)
    if active_only:
        query = query.eq("is_active", True)
    if kind:
        query = query.eq("kind", kind)
    response = query.execute()
    _raise_for_error(response)
    return response.data or []


def add_event(person_id, category_id, note=None):
    client = get_client()
    payload = {
        "person_id": person_id,
        "category_id": category_id,
        "note": note,
    }
    response = client.table("events").insert(payload).execute()
    _raise_for_error(response)
    return response.data


def delete_event(event_id):
    client = get_client()
    response = client.table("events").delete().eq("id", event_id).execute()
    _raise_for_error(response)
    return response.data


def get_events(person_id=None, category_id=None, start_at=None, end_at=None):
    client = get_client()
    query = client.table("events").select(
        "id,person_id,category_id,event_at,note,people(id,display_name,alias),categories(id,name,kind,points)"
    ).order("event_at", desc=True)

    if person_id:
        query = query.eq("person_id", person_id)
    if category_id:
        query = query.eq("category_id", category_id)
    if start_at:
        query = query.gte("event_at", start_at.isoformat())
    if end_at:
        query = query.lte("event_at", end_at.isoformat())

    response = query.execute()
    _raise_for_error(response)

    events = []
    for row in response.data or []:
        person = row.get("people") or {}
        category = row.get("categories") or {}
        events.append(
            {
                "id": row.get("id"),
                "event_at": row.get("event_at"),
                "person_id": row.get("person_id"),
                "category_id": row.get("category_id"),
                "person_name": person.get("display_name"),
                "alias": person.get("alias"),
                "category_name": category.get("name"),
                "category_kind": category.get("kind"),
                "category_points": category.get("points"),
                "note": row.get("note"),
            }
        )
    return events


def get_rankings(start_at=None, end_at=None):
    events = get_events(start_at=start_at, end_at=end_at)
    totals = {}

    for event in events:
        key = event.get("person_id")
        if not key:
            continue
        if key not in totals:
            totals[key] = {
                "person_name": event.get("person_name"),
                "total_points": 0,
                "event_count": 0,
            }
        totals[key]["total_points"] += event.get("category_points") or 0
        totals[key]["event_count"] += 1

    return list(totals.values())
