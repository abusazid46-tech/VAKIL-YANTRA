-- Matter notes and tasks for dashboard and matter workspace.

create table if not exists matter_notes (
  id varchar(48) primary key,
  firm_id varchar(48) not null references firms(id) on delete cascade,
  matter_id varchar(48) not null references matters(id) on delete cascade,
  body text not null,
  created_by varchar(48) not null references users(id),
  created_at timestamptz not null default now()
);

create table if not exists matter_tasks (
  id varchar(48) primary key,
  firm_id varchar(48) not null references firms(id) on delete cascade,
  matter_id varchar(48) not null references matters(id) on delete cascade,
  title varchar(240) not null,
  due_date date,
  status varchar(32) not null default 'open',
  assigned_to_user_id varchar(48) references users(id),
  created_by varchar(48) not null references users(id),
  created_at timestamptz not null default now()
);

alter table matter_notes enable row level security;
alter table matter_tasks enable row level security;
alter table matter_notes force row level security;
alter table matter_tasks force row level security;

drop policy if exists tenant_select_matter_notes on matter_notes;
drop policy if exists tenant_insert_matter_notes on matter_notes;
create policy tenant_select_matter_notes on matter_notes
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_matter_notes on matter_notes
  for insert with check (firm_id = current_setting('app.current_firm_id', true));

drop policy if exists tenant_select_matter_tasks on matter_tasks;
drop policy if exists tenant_insert_matter_tasks on matter_tasks;
drop policy if exists tenant_update_matter_tasks on matter_tasks;
create policy tenant_select_matter_tasks on matter_tasks
  for select using (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_insert_matter_tasks on matter_tasks
  for insert with check (firm_id = current_setting('app.current_firm_id', true));
create policy tenant_update_matter_tasks on matter_tasks
  for update using (firm_id = current_setting('app.current_firm_id', true))
  with check (firm_id = current_setting('app.current_firm_id', true));

create index if not exists idx_matter_notes_firm_matter on matter_notes(firm_id, matter_id);
create index if not exists idx_matter_tasks_firm_matter on matter_tasks(firm_id, matter_id);
create index if not exists idx_matter_tasks_due_date on matter_tasks(firm_id, due_date);
