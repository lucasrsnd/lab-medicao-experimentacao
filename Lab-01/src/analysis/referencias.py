"""Fonte de referência única para "linguagens mais populares" (RQ05/RQ07), usada
em todo o laboratório - GitHub Octoverse (fonte já escolhida pelo DaviSantos23, ver
`scripts/README_DaviSantos23.md`). Lista fixa porque o Octoverse é um relatório
anual publicado, não um serviço consultável por API.

Fonte: Octoverse 2025 - "AI leads TypeScript to #1"
https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/
(rankeado por contribuidores mensais distintos, agosto/2025 - consultado em 2026-08-18)
"""

OCTOVERSE_EDICAO = "2025"
OCTOVERSE_FONTE_URL = (
    "https://github.blog/news-insights/octoverse/"
    "octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/"
)

# Top 10 do Octoverse 2025, nesta ordem de popularidade (contribuidores mensais).
OCTOVERSE_TOP_LINGUAGENS = [
    "TypeScript",
    "Python",
    "JavaScript",
    "Java",
    "C#",
    "PHP",
    "Shell",
    "C++",
    "HCL",
    "Go",
]
