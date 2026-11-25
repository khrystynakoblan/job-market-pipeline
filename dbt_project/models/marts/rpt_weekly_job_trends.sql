with weeks as (
    select generate_series(
        date_trunc('week', current_date) - interval '25 weeks',
        date_trunc('week', current_date),
        interval '1 week'
    )::date as week_start
),

weekly_counts as (
    select
        date_trunc('week', date_posted)::date as week_start,
        count(job_key) as job_count
    from {{ ref('fct_job_postings') }}
    group by date_trunc('week', date_posted)::date
)

select
    weeks.week_start,
    coalesce(weekly_counts.job_count, 0) as job_count
from weeks
left join weekly_counts
    on weeks.week_start = weekly_counts.week_start
order by weeks.week_start
