# {{ exam.info.title.to_markdown() }}

{{ exam.info.description.to_markdown() }}

{% set real_question_count = namespace(value=0) %}
{% for question in exam.questions %}
    {% if question is multiple_choice %}
        {% set real_question_count.value = real_question_count.value + 1 %}
		{% with question=question, question_index=real_question_count.value %}
			{% include 'multiple_choice_question.md' %}
		{% endwith %}
	{% elif question is open %}
        {% set real_question_count.value = real_question_count.value + 1 %}
		{% with question=question, question_index=real_question_count.value %}
			{% include 'open_question.md' %}
		{% endwith %}
	{% elif question is multiple_response %}
        {% set real_question_count.value = real_question_count.value + 1 %}
		{% with question=question, question_index=real_question_count.value %}
			{% include 'multiple_response_question.md' %}
		{% endwith %}
	{% elif question is text_only %}
		{% with question=question, question_index=loop.index %}
			{% include 'text_only_question.md' %}
		{% endwith %}
	{% endif %}


{% endfor %}
