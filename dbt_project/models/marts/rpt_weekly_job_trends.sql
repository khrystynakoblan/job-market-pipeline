select
    date_trunc('week', date_posted)::date as week_start,
    count(job_key) as job_count
from {{ ref('fct_job_postings') }}
group by date_trunc('week', date_posted)::date
order by week_start
