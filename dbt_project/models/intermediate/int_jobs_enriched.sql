with staged as (
    select *
    from {{ ref('stg_jobs') }}
),

-- the same employer appears with different casing (e.g. "Adecco" / "ADECCO"),
-- so each case-insensitive name is mapped to its most frequent spelling
company_name_variants as (
    select
        lower(trim(company_name)) as company_name_key,
        trim(company_name) as company_name,
        count(*) as variant_count
    from staged
    where company_name is not null
    group by lower(trim(company_name)), trim(company_name)
),

canonical_company_names as (
    select distinct on (company_name_key)
        company_name_key,
        company_name as canonical_company_name
    from company_name_variants
    order by
        company_name_key asc,
        variant_count desc,
        (company_name = upper(company_name)) asc,
        company_name asc
)

select
    staged.job_key,
    staged.job_id,
    staged.category,
    staged.contract_type,
    staged.latitude,
    staged.longitude,
    staged.salary_min,
    staged.salary_max,
    staged.is_salary_predicted,
    staged.date_posted,
    staged.job_url,
    staged.description,
    staged.source_file,
    canonical_company_names.canonical_company_name as company_name,

    trim(staged.job_title) as job_title,

    -- location_area is the Adzuna hierarchy, e.g. ["UK", "North West England",
    -- "Greater Manchester", "Manchester", "Rusholme"]: London districts roll up
    -- to London, deeper levels below the town are neighbourhoods, and entries
    -- with only country or region have no city
    case
        when staged.location_area ->> 1 = 'London' then 'London'
        when coalesce(jsonb_array_length(staged.location_area), 0) <= 2 then 'Unspecified'
        when jsonb_array_length(staged.location_area) = 3 then staged.location_area ->> 2
        else staged.location_area ->> 3
    end as city,
    coalesce(staged.location_area ->> 1, 'Unspecified') as region,

    case
        when staged.salary_min is not null and staged.salary_max is not null
            then (staged.salary_min + staged.salary_max) / 2.0
    end as salary_avg

from staged
left join canonical_company_names
    on lower(trim(staged.company_name)) = canonical_company_names.company_name_key
