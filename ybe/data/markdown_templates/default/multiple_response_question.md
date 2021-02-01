## Question \VAR{question_index} (points: \VAR{question.points})

\VAR{question.text.to_markdown()}
\BLOCK{ for answer in question.answers }
- \VAR{ answer.text.to_markdown() }
\BLOCK{ endfor }

