CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE candidates (
  candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT,
  email TEXT,
  phone TEXT,
  
  job_title TEXT,
  date_of_application DATE,
  current_location TEXT,
  preferred_locations TEXT,
  total_experience TEXT,
  current_employer TEXT,
  current_designation TEXT,
  role TEXT,
  industry TEXT,
  annual_salary NUMERIC,
  notice_period TEXT,
  ug_degree TEXT,
  ug_university TEXT,
  ug_graduation_year TEXT,
  pg_degree TEXT,
  pg_university TEXT,
  pg_graduation_year TEXT,
  gender TEXT,
  marital_status TEXT,
  home_town TEXT,
  date_of_birth DATE,

  experience_summary TEXT,
  core_technical_skills JSONB,
  education_certification TEXT,

  resume_file_name TEXT,
  parsed_resume TEXT,
  specialized_technical_skills JSONB,
  current_project TEXT,
  other_notable_projects JSONB,
  potential_flags JSONB,
  resume_notes TEXT,
  interview_transcript TEXT,
  scorecard JSONB,
  evaluation_summary TEXT,
  recommendation TEXT,
  status TEXT,
  scheduled_time TIMESTAMPTZ,

  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);