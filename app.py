import streamlit as st
from datetime import datetime, timedelta, timezone, time
import pandas as pd
import db

st.set_page_config(page_title="Nicolometro", layout="centered")

st.title("Nicolometro")

USERS = {
    "manuelcorrealuna@gmail.com": "12345678",
    "nmoreno@sanisidro.gob.ar": "12345678",
}


def _require_login():
    if st.session_state.get("authenticated"):
        return

    st.subheader("Iniciar sesion")
    email = st.text_input("Email")
    password = st.text_input("Contrasena", type="password")
    if st.button("Entrar"):
        if USERS.get(email) == password:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Credenciales invalidas.")

    st.stop()


_require_login()

PAGES = [
    "Registrar comportamiento",
    "Ranking",
    "Historial",
    "Personas",
]

page = st.sidebar.radio("Navegacion", PAGES)


def _to_utc_datetime(d, end_of_day=False):
    if d is None:
        return None
    t = time.max if end_of_day else time.min
    return datetime.combine(d, t, tzinfo=timezone.utc)


def _date_range_selector(prefix=""):
    options = ["Todo el historial", "Ultimos 7 dias", "Ultimos 30 dias", "Rango personalizado"]
    choice = st.selectbox(f"{prefix}Rango de fechas", options)
    now = datetime.now(timezone.utc)

    if choice == "Todo el historial":
        return None, None
    if choice == "Ultimos 7 dias":
        return now - timedelta(days=7), now
    if choice == "Ultimos 30 dias":
        return now - timedelta(days=30), now

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(f"{prefix}Desde")
    with col2:
        end_date = st.date_input(f"{prefix}Hasta")

    return _to_utc_datetime(start_date), _to_utc_datetime(end_date, end_of_day=True)

KIND_LABELS = {"good": "Positivo", "bad": "Negativo"}


if page == "Personas":
    st.subheader("Personas")

    with st.form("person_form", clear_on_submit=True):
        display_name = st.text_input("Nombre visible *")
        alias = st.text_input("Alias (opcional)")
        submitted = st.form_submit_button("Crear persona")

    if submitted:
        if not display_name.strip():
            st.error("El nombre visible es obligatorio.")
        else:
            try:
                db.add_person(display_name.strip(), alias.strip() or None)
                st.success("Persona creada.")
            except Exception as exc:
                st.error(f"No se pudo crear la persona: {exc}")

    try:
        people = db.get_people()
    except Exception as exc:
        st.error(f"No se pudo cargar la lista: {exc}")
        people = []

    if people:
        display_people = []
        for person in people:
            display_people.append(
                {
                    "Persona": person.get("display_name"),
                    "Alias": person.get("alias"),
                }
            )
        st.dataframe(display_people, use_container_width=True)
    else:
        st.info("No hay personas registradas.")


elif page == "Registrar comportamiento":
    st.subheader("Registrar comportamiento")

    try:
        people = db.get_people()
        categories = db.get_categories(active_only=True)
    except Exception as exc:
        st.error(f"No se pudieron cargar los datos: {exc}")
        people = []
        categories = []

    if not people:
        st.info("Crea una persona antes de registrar comportamiento.")
    elif not categories:
        st.info("No hay categorias activas disponibles.")
    else:
        people_labels = {p["display_name"]: p["id"] for p in people}
        category_labels = {f"{c['name']} ({c['points']} pts)": c["id"] for c in categories}

        with st.form("event_form", clear_on_submit=True):
            person_name = st.selectbox("Persona", list(people_labels.keys()))
            category_name = st.selectbox("Categoria", list(category_labels.keys()))
            note = st.text_area("Nota (opcional)")
            submitted = st.form_submit_button("Registrar")

        if submitted:
            person_id = people_labels.get(person_name)
            category_id = category_labels.get(category_name)

            if not person_id or not category_id:
                st.error("Selecciona una persona y una categoria validas.")
            else:
                try:
                    db.add_event(person_id, category_id, note.strip() or None)
                    st.success("Registro guardado.")
                except Exception as exc:
                    st.error(f"No se pudo registrar: {exc}")


elif page == "Ranking":
    st.subheader("Ranking")

    start_at, end_at = _date_range_selector()

    try:
        ranking = db.get_rankings(start_at=start_at, end_at=end_at)
    except Exception as exc:
        st.error(f"No se pudo calcular el ranking: {exc}")
        ranking = []

    if not ranking:
        st.info("No hay eventos en el rango seleccionado.")
    else:
        best = sorted(ranking, key=lambda x: x["total_points"], reverse=True)
        worst = sorted(ranking, key=lambda x: x["total_points"])

        st.markdown("### Top Mejores Personas")
        best_display = []
        for row in best:
            best_display.append(
                {
                    "Persona": row.get("person_name"),
                    "Puntaje Total": row.get("total_points"),
                    "Eventos registrados": row.get("event_count"),
                }
            )
        st.dataframe(best_display, use_container_width=True)

        top10_best = best[:10]
        if top10_best:
            chart_data = pd.DataFrame(
                [{"Persona": r.get("person_name"), "Puntaje Total": r.get("total_points")} for r in top10_best]
            ).set_index("Persona")
            st.bar_chart(chart_data)

        st.markdown("### Top Peores Personas")
        worst_display = []
        for row in worst:
            worst_display.append(
                {
                    "Persona": row.get("person_name"),
                    "Puntaje Total": row.get("total_points"),
                    "Eventos registrados": row.get("event_count"),
                }
            )
        st.dataframe(worst_display, use_container_width=True)

        low10_worst = worst[:10]
        if low10_worst:
            chart_data = pd.DataFrame(
                [{"Persona": r.get("person_name"), "Puntaje Total": r.get("total_points")} for r in low10_worst]
            ).set_index("Persona")
            st.bar_chart(chart_data)


elif page == "Historial":
    st.subheader("Historial")

    try:
        people = db.get_people()
        categories = db.get_categories(active_only=False)
    except Exception as exc:
        st.error(f"No se pudieron cargar los datos: {exc}")
        people = []
        categories = []

    person_options = ["Todas"] + [p["display_name"] for p in people]
    category_options = ["Todas"] + [c["name"] for c in categories]

    selected_person = st.selectbox("Persona", person_options)
    selected_category = st.selectbox("Categoria", category_options)

    use_dates = st.checkbox("Filtrar por fechas")
    start_at = end_at = None
    if use_dates:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Desde")
        with col2:
            end_date = st.date_input("Hasta")
        start_at = _to_utc_datetime(start_date)
        end_at = _to_utc_datetime(end_date, end_of_day=True)

    person_id = None
    if selected_person != "Todas":
        person_id = next((p["id"] for p in people if p["display_name"] == selected_person), None)

    category_id = None
    if selected_category != "Todas":
        category_id = next((c["id"] for c in categories if c["name"] == selected_category), None)

    try:
        events = db.get_events(person_id=person_id, category_id=category_id, start_at=start_at, end_at=end_at)
    except Exception as exc:
        st.error(f"No se pudo cargar el historial: {exc}")
        events = []

    if events:
        display_events = []
        for event in events:
            display_events.append(
                {
                    "Persona": event.get("person_name"),
                    "Alias": event.get("alias"),
                    "Categoría": event.get("category_name"),
                    "Tipo de Categoría": KIND_LABELS.get(event.get("category_kind"), event.get("category_kind")),
                    "Puntaje": event.get("category_points"),
                    "Nota": event.get("note"),
                }
            )
        st.dataframe(display_events, use_container_width=True)
    else:
        st.info("No hay eventos para mostrar.")

    if db.is_admin_mode() and events:
        st.markdown("### Administrar eventos")
        event_lookup = {
            f"{e['event_at']} - {e['person_name']} - {e['category_name']}": e["id"] for e in events
        }
        selected_event = st.selectbox("Evento para eliminar", list(event_lookup.keys()))
        if st.button("Eliminar evento"):
            try:
                db.delete_event(event_lookup[selected_event])
                st.success("Evento eliminado.")
            except Exception as exc:
                st.error(f"No se pudo eliminar: {exc}")
