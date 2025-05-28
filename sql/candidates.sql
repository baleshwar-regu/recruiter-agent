CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE candidates (
  candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  email TEXT UNIQUE,
  phone TEXT UNIQUE,
  resume_file_name TEXT,
  parsed_resume TEXT,
  experience_summary TEXT,
  core_technical_skills JSONB,
  specialized_technical_skills JSONB,
  current_project TEXT,
  other_notable_projects JSONB,
  education_certification TEXT,
  potential_flags JSONB,
  resume_notes TEXT,
  interview_transcript TEXT,
  scorecard JSONB,
  evaluation_summary TEXT,
  recommendation TEXT,
  status TEXT,
  scheduled_time TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);