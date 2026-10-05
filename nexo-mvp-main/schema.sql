-- NEXO Qualifica+ — esquema mínimo para evolução do MVP em Supabase/PostgreSQL

create table if not exists participants (
  id text primary key,
  name text not null,
  age integer,
  education text,
  employment_status text,
  digital_access text,
  created_at timestamptz default now()
);

create table if not exists companies (
  id text primary key,
  name text not null,
  sector text,
  created_at timestamptz default now()
);

create table if not exists demands (
  id bigserial primary key,
  company_id text references companies(id),
  description text not null,
  status text default 'active',
  created_at timestamptz default now()
);

create table if not exists skills (
  id text primary key,
  name text not null,
  skill_type text,
  version integer default 1,
  active boolean default true
);

create table if not exists demand_skills (
  id bigserial primary key,
  demand_id bigint references demands(id) on delete cascade,
  skill_id text references skills(id),
  confidence numeric,
  validation_status text default 'pending',
  validated_by text,
  validated_at timestamptz
);

create table if not exists participant_skills (
  id bigserial primary key,
  participant_id text references participants(id) on delete cascade,
  skill_id text references skills(id),
  level numeric,
  source text,
  assessed_at timestamptz default now()
);

create table if not exists barriers (
  id bigserial primary key,
  participant_id text references participants(id) on delete cascade,
  barrier_type text not null,
  description text,
  active boolean default true,
  created_at timestamptz default now()
);

create table if not exists recommendations (
  id bigserial primary key,
  participant_id text references participants(id),
  demand_id bigint references demands(id),
  pathway text not null,
  rationale text,
  readiness numeric,
  model_version text default 'rules_v1',
  human_decision text,
  human_reason text,
  decided_by text,
  created_at timestamptz default now()
);

create table if not exists interventions (
  id bigserial primary key,
  participant_id text references participants(id),
  recommendation_id bigint references recommendations(id),
  intervention_type text,
  title text,
  started_at timestamptz,
  completed_at timestamptz,
  status text default 'planned'
);

create table if not exists trajectory_events (
  id bigserial primary key,
  participant_id text references participants(id),
  event_type text not null,
  label text,
  actor text,
  payload jsonb,
  occurred_at timestamptz default now()
);

create table if not exists assessments (
  id bigserial primary key,
  participant_id text references participants(id),
  intervention_id bigint references interventions(id),
  skill_id text references skills(id),
  score numeric,
  demonstrated boolean,
  evidence_source text,
  assessed_at timestamptz default now()
);

create table if not exists outcomes (
  id bigserial primary key,
  participant_id text references participants(id),
  outcome_type text not null,
  status text default 'candidate',
  value jsonb,
  observed_at timestamptz,
  validated_at timestamptz
);

create table if not exists experiments (
  id bigserial primary key,
  name text not null,
  hypothesis text not null,
  status text default 'planned',
  created_at timestamptz default now()
);

create table if not exists experiment_cohorts (
  id bigserial primary key,
  experiment_id bigint references experiments(id) on delete cascade,
  name text not null,
  intervention_description text,
  sample_size integer,
  metrics jsonb
);

create table if not exists evidence_log (
  id bigserial primary key,
  event_type text not null,
  actor text,
  source text,
  description text,
  payload jsonb,
  evidence_hash text,
  created_at timestamptz default now()
);
