with staged as (
    select *
    from {{ ref('stg_jobs') }}
)

select
    job_key,
    job_id,

    trim(job_title) as job_title,
    trim(company_name) as company_name,

    category,
    contract_type,

    trim(split_part(location_name, ',', 1)) as city,
    nullif(trim(split_part(location_name, ',', 2)), '') as region,
    latitude,
    longitude,

    salary_min,
    salary_max,
    case
        when salary_min is not null and salary_max is not null
            then (salary_min + salary_max) / 2.0
        else null
    end as salary_avg,
    is_salary_predicted,

    date_posted,
    job_url,
    description,
    source_file

from staged
