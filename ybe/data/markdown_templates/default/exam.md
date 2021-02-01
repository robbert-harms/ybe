# \VAR{exam.info.title.to_markdown()}

\VAR{exam.info.description.to_markdown()}

\BLOCK{ set real_question_count = namespace(value=0) }
\BLOCK{ for question in exam.questions }
    \BLOCK{ if question is multiple_choice }
        \BLOCK{ set real_question_count.value = real_question_count.value + 1 }
		\BLOCK{ with question=question, question_index=real_question_count.value }
			\BLOCK{ include 'multiple_choice_question.md' }
		\BLOCK{ endwith }
	\BLOCK{ elif question is open }
        \BLOCK{ set real_question_count.value = real_question_count.value + 1 }
		\BLOCK{ with question=question, question_index=real_question_count.value }
			\BLOCK{ include 'open_question.md' }
		\BLOCK{ endwith }
	\BLOCK{ elif question is multiple_response }
        \BLOCK{ set real_question_count.value = real_question_count.value + 1 }
		\BLOCK{ with question=question, question_index=real_question_count.value }
			\BLOCK{ include 'multiple_response_question.md' }
		\BLOCK{ endwith }
	\BLOCK{ elif question is text_only }
		\BLOCK{ with question=question, question_index=loop.index }
			\BLOCK{ include 'text_only_question.md' }
		\BLOCK{ endwith }
	\BLOCK{ endif }
\BLOCK{ endfor }
