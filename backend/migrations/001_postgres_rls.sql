-- Vakil Yantra PostgreSQL baseline with tenant RLS.
-- Run after SQLAlchemy/Alembic creates the tables, or convert this into Alembic operations.

create extension if not exists pgcrypto;
create extension if not exists vector;

alter table matters enable row level security;
alter table documents enable row level security;
alter table ai_runs enable row level security;
alter table audit_events enable row level security;

alter table matters force row level security;
alter table documents force row level security;
alter table ai_runs force row level security;
alter table audit_events force row level security;

drop policy if exists tenant_select_matters on matters;
drop policy if exists tenant_insert_matters on matters;
drop policy if exists tenant_update_matters on matters;
create policy tenant_select_matters on matters
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_matters on matters
  for insert with check (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_update_matters on matters
  for update using (firm_id = current_setting('app.current_firm_id', true))
  with check (firm_id = current_setting('app.current_firm_id', true));

drop policy if exists tenant_select_documents on documents;
drop policy if exists tenant_insert_documents on documents;
drop policy if exists tenant_update_documents on documents;
create policy tenant_select_documents on documents
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_documents on documents
  for insert with check (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_update_documents on documents
  for update using (firm_id = current_setting('app.current_firm_id', true))
  with check (firm_id = current_setting('app.current_firm_id', true));

drop policy if exists tenant_select_ai_runs on ai_runs;
drop policy if exists tenant_insert_ai_runs on ai_runs;
create policy tenant_select_ai_runs on ai_runs
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_ai_runs on ai_runs
  for insert with check (firm_id = current_setting('app.current_firm_id', true));

drop policy if exists tenant_select_audit_events on audit_events;
drop policy if exists tenant_insert_audit_events on audit_events;
create policy tenant_select_audit_events on audit_events
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_audit_events on audit_events
  for insert with check (firm_id = current_setting('app.current_firm_id', true));

create index if not exists idx_matters_firm_id on matters(firm_id);
create index if not exists idx_documents_firm_id on documents(firm_id);
create index if not exists idx_ai_runs_firm_id on ai_runs(firm_id);
create index if not exists idx_audit_events_firm_id on audit_events(firm_id);
