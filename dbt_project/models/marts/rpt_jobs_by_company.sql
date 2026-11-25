with company_counts as (
    select
        companies.company_name,
        count(fct.job_key) as job_count
    from {{ ref('fct_job_postings') }} as fct
    inner join {{ ref('dim_companies') }} as companies
        on fct.company_key = companies.company_key
    group by companies.company_name
),

ranked_companies as (
    select
        company_name,
        job_count,
        row_number() over (order by job_count desc, company_name asc) as company_rank
    from company_counts
)

select
    company_name,
    job_count,
    company_rank
from ranked_companies
where company_rank <= 8
order by company_rank
