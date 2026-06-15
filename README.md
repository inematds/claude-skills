# ⚡ Claude Skills na Prática

Curso completo e prático sobre **construir Agent Skills do Claude Code** — do
`SKILL.md` à arquitetura multi-agente. Site estático, publicado no GitHub Pages.

🔗 **Curso ao vivo:** https://inematds.github.io/claude-skills/
🔗 **Portal:** [INEMA.CLUB](https://inema.club)

## Trilhas

| # | Trilha | Módulos |
|---|--------|---------|
| 1 | 🧬 Fundamentos de Agent Skills | Anatomia · Progressive disclosure · Descriptions que disparam |
| 2 | 🚀 Construindo Sua Primeira Skill | Dissecando um gerador de itinerários · Setup flow → HTML |
| 3 | 🎨 Skills de Frontend & Geração | Vibe Coding · Funnel Builder |
| 4 | ⚙️ Skills de Automação & Dados | n8n Reviewer · Local Leads · Lead Scoring (Apify) |
| 5 | 💼 Skills de Consultoria AI | Onboarding + Audit · SEO/AEO Auditor · RAG Architect |
| 6 | 🧠 Arquitetura Avançada de Skills | Improvised Intelligence · Taproot · Multi-Agent Memory |

**16 módulos · 96 tópicos · 12 skills reais para download.**

## Estrutura

```
index.html              # Landing
skills.html             # Central de Skills (download + instalação)
curso/trilhaN/          # Index da trilha + módulos (modulo-N-M.html)
skills/                 # Arquivos das skills (.skill / .md / .py)
```

## Como rodar localmente

Site self-contained (Tailwind via CDN). Basta servir a pasta:

```bash
python3 -m http.server 8080   # depois abra http://localhost:8080
```

---

Conteúdo educacional · 2026 · INEMA.CLUB
