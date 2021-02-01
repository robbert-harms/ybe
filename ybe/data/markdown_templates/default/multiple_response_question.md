{% if question.title is none %}
## Question {{ question_index }} (points: {{ question.points }})
{% else %}
## Question {{ question_index }}: {{ question.title.to_markdown() }} (points: {{ question.points }})
{% endif %}

{{ question.text.to_markdown() }}

{% for answer in question.answers %}
{{loop.index}}. {{ answer.text.to_markdown() }}
{% endfor %}

