with city_salaries as (
    select
        locations.city,
        count(fct.job_key) as job_count,
        round(avg(fct.salary_avg)::numeric, 2) as avg_salary,
        round(min(fct.salary_min)::numeric, 2) as min_salary,
        round(max(fct.salary_max)::numeric, 2) as max_salary,
        round(
            percentile_cont(0.5) within group (order by fct.salary_avg)::numeric,
            2
        ) as median_salary
    from {{ ref('fct_job_postings') }} as fct
    inner join {{ ref('dim_locations') }} as locations
        on fct.location_key = locations.location_key
    where
        fct.salary_avg is not null
        and locations.city <> 'Unspecified'
    group by locations.city
),

ranked_cities as (
    select
        city,
        job_count,
        avg_salary,
        min_salary,
        max_salary,
        median_salary,
        row_number() over (order by job_count desc, city asc) as city_rank
    from city_salaries
)

select
    city,
    job_count,
    avg_salary,
    min_salary,
    max_salary,
    median_salary,
    city_rank
from ranked_cities
where city_rank <= 10
order by city_rank
