select
    companies.company_name,
    count(fct.job_key) as job_count
from {{ ref('fct_job_postings') }} as fct
inner join {{ ref('dim_companies') }} as companies
    on fct.company_key = companies.company_key
group by companies.company_name
order by job_count desc
