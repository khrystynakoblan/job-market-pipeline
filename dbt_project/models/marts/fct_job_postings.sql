select
    jobs.job_key,
    jobs.job_id,
    jobs.job_title,

    companies.company_key,
    locations.location_key,

    jobs.category,
    jobs.contract_type,

    jobs.latitude,
    jobs.longitude,

    jobs.salary_min,
    jobs.salary_max,
    jobs.salary_avg,
    jobs.is_salary_predicted,

    jobs.date_posted,
    jobs.job_url,
    jobs.description,
    jobs.source_file

from {{ ref('int_jobs_enriched') }} as jobs

inner join {{ ref('dim_companies') }} as companies
    on jobs.company_name = companies.company_name

inner join {{ ref('dim_locations') }} as locations
    on jobs.city = locations.city
    and jobs.region is not distinct from locations.region
