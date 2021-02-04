{% if question.title is none %}
## Information
{% else %}
## {{ question.title.to_markdown() }}
{% endif %}

{{ question.text.to_markdown() }}

