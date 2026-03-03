-- Sprint A: crear tabla actividad en Supabase
-- Ejecutar en Supabase → SQL Editor → New query → Pegar y Run

create table if not exists public.actividad (
  id uuid primary key default gen_random_uuid(),
  fecha timestamptz not null default now(),
  tipo text not null check (tipo in ('carga_balance', 'analisis_renta')),
  descripcion text,
  resultado_contable bigint,
  rli bigint,
  impuesto bigint,
  regimen text,
  archivo_guardado text
);

create index if not exists idx_actividad_fecha on public.actividad (fecha desc);
create index if not exists idx_actividad_tipo on public.actividad (tipo);

alter table public.actividad enable row level security;

create policy "Permitir todo para anon (uso con API key)"
  on public.actividad for all
  to anon
  using (true)
  with check (true);
