select distinct
    {{ dbt_utils.generate_surrogate_key(['city', 'region']) }} as location_key,
    city,
    region

from {{ ref('int_jobs_enriched') }}

where city is not null
