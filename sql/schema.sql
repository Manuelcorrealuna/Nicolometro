create extension if not exists "pgcrypto";

create table if not exists people (
  id uuid primary key default gen_random_uuid(),
  display_name text not null,
  alias text null,
  created_at timestamptz default now()
);

create table if not exists categories (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  kind text not null check (kind in ('good', 'bad')),
  points int not null,
  is_active boolean default true
);

create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  person_id uuid references people(id),
  category_id uuid references categories(id),
  event_at timestamptz default now(),
  note text null
);

insert into categories (name, kind, points, is_active)
values
  ('Paladín Ejemplar', 'good', 3, true),
  ('Ciudadano Modelo', 'good', 2, true),
  ('Alma Bienintencionada', 'good', 1, true),
  ('Villano Malévolo', 'bad', -3, true),
  ('Agente del Caos', 'bad', -2, true),
  ('Sospechoso Habitual', 'bad', -1, true)
on conflict do nothing;
