with raw_data as (
    select
        payload,
        source_file
    from {{ source('raw_zone', 'jobs_raw') }}
)

select
    {{ dbt_utils.generate_surrogate_key(["payload->>'id'"]) }} as job_key,
    
    (payload->>'id')::varchar as job_id,
    
    (payload->>'title')::varchar as job_title,
    (payload->'company'->>'display_name')::varchar as company_name,
    (payload->'category'->>'label')::varchar as category,
    (payload->>'contract_type')::varchar as contract_type,
    
    (payload->'location'->>'display_name')::varchar as location_name,
    (payload->>'latitude')::numeric as latitude,
    (payload->>'longitude')::numeric as longitude,
    
    (payload->>'salary_min')::numeric as salary_min,
    (payload->>'salary_max')::numeric as salary_max,
    
    case 
        when (payload->>'salary_is_predicted') = '1' then true
        else false
    end as is_salary_predicted,
    
    -- Дати та метадані
    (payload->>'created')::timestamp as date_posted,
    (payload->>'redirect_url')::varchar as job_url,
    (payload->>'description')::text as description,
    
    source_file
    
from raw_data