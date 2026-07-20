select distinct
    {{ dbt_utils.generate_surrogate_key(['company_name']) }} as company_key,
    company_name

from {{ ref('int_jobs_enriched') }}

where company_name is not null
