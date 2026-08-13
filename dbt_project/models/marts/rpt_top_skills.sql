with skill_catalog as (
    select unnest(array[
        'python',
        'sql',
        'spark',
        'airflow',
        'dbt',
        'kafka',
        'aws',
        'docker',
        'kubernetes',
        'postgresql',
        'scala',
        'java',
        'etl',
        'snowflake',
        'bigquery',
        'terraform',
        'pandas',
        'pyspark',
        'looker',
        'tableau'
    ]) as skill
),

job_skill_matches as (
    select
        jobs.job_key,
        skills.skill
    from {{ ref('fct_job_postings') }} as jobs
    cross join skill_catalog as skills
    where lower(
        coalesce(jobs.description, '') || ' ' || coalesce(jobs.job_title, '')
    ) like '%' || skills.skill || '%'
),

ranked_skills as (
    select
        skill,
        count(distinct job_key) as job_count,
        row_number() over (order by count(distinct job_key) desc) as skill_rank
    from job_skill_matches
    group by skill
)

select
    skill,
    job_count,
    skill_rank
from ranked_skills
where skill_rank <= 10
