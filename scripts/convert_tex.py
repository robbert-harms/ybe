__author__ = 'Robbert Harms'
__date__ = '2020-04-10'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'
__licence__ = 'GPL v3'


from pylatexenc.latexwalker import LatexWalker, LatexEnvironmentNode
w = LatexWalker("""
\documentclass{article}
\newenvironment{question}[2]{}{}
\newenvironment{answers}{\begin{itemize}}{\end{itemize}}
\newcommand\answerinfo[1]{}
\newcommand\metadata[1]{}
\newcommand\analytics[1]{}

\begin{document}

\title{Example questions database}
\author{Robber Harms and Sanne Schoenmakers}
\maketitle

\begin{question}{multiple_choice}{#2020_01}
Romantic relationships are the spice of life, they make us feel alive in a way that nothing else can. Genuine romance exists when two people show that they care for each other through small acts of love and affection. We feel loved and cared for when we know that our significant other is thinking about how to give us the most pleasure. Romance is the key to keeping the sparks flying. Without it, any relationship will soon lose its shine.

How nice is Robbert?

\begin{answers}
	\item Stupid
		\answerinfo{points=-1}
	\item Ok.
		\answerinfo{points=0.2}
	\item Nice
	\item Supernice
		\answerinfo{correct,points=1}
\end{answers}

\metadata{
	thinking_type = knowledge
	related_concepts = [Brains, Body, Behaviour]
	chapter = 1
	difficulty = 10
}

\analytics{
- 2020_qz1:
	participants: 1
	nmr_correct: 0
- 2020_qz1:
	participants: 200
	nmr_correct: 25
}
\end{question}

\end{document}

""")

(nodelist, pos, len_) = w.get_latex_nodes(pos=0)

print()
