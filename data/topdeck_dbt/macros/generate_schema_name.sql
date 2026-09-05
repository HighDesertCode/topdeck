{#
  Override dbt's default schema naming. The default prefixes custom schemas
  with the profile schema (core_staging); we want the names verbatim:
  staging, core, api.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
