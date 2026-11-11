# CLAUDE.md — job-match-assistant

Guía para Claude Code (y para cualquier persona) que trabaje en este repositorio.
Plan completo: https://claude.ai/artifact/BEkaisi9t8oUovmqH3edtv

## Qué es este proyecto

Asistente de búsqueda de empleo para ciencia de datos. Recolecta vacantes desde APIs
oficiales, extrae las habilidades que piden con NLP, compara cada vacante con el CV del
usuario mediante RAG y muestra tendencias (skills, salarios, modalidad) en un dashboard.

Es un proyecto de portafolio: el código, los tests, las métricas y el README deben verse
profesionales, porque los leerán reclutadores.

Responde y comenta en **español**. Código, nombres de variables, commits y README principal
en **inglés** (con una sección en español en el README).

## Arquitectura

```
Fuentes (APIs + Kaggle) → Ingesta (ETL) → Limpieza y skills (NLP) → PostgreSQL + pgvector
                                                                         │
                         Tu CV (PDF, Docling) → Match + RAG (Ollama) ◄───┤
                                                     │                   │
                              Dashboard (TypeScript) ◄── FastAPI ◄───────┘
```

## Stack

| Capa | Herramienta |
| --- | --- |
| Gestión de entorno | `uv` (Python 3.11+) |
| Ingesta | `httpx`, `pydantic` |
| Almacenamiento | PostgreSQL + pgvector (Docker) |
| Transformación | `pandas` o `polars`, SQL |
| NLP | spaCy (`PhraseMatcher`), sentence-transformers |
| CV | Docling |
| RAG / LLM | Ollama (modelo local, p. ej. Llama 3.x o Qwen) |
| API | FastAPI |
| Dashboard | TypeScript, Next.js (o Vite + React), Recharts |
| Calidad | `pytest`, `ruff`, `pre-commit`, GitHub Actions |
| Orquestación | GitHub Actions con `cron` |

## Estructura del repositorio

```text
job-match-assistant/
├── CLAUDE.md
├── README.md
├── docker-compose.yml        # Postgres + pgvector, API, Ollama
├── .env.example              # claves de API (sin valores reales)
├── .github/workflows/
│   ├── ci.yml                # lint + tests
│   └── ingest.yml            # cron diario de ingesta
├── backend/
│   ├── pyproject.toml
│   ├── src/jobmatch/
│   │   ├── ingest/           # remotive.py, adzuna.py, kaggle.py
│   │   ├── transform/        # limpieza, dedupe, salarios, seniority
│   │   ├── nlp/              # taxonomía y extractor de skills
│   │   ├── match/            # CV, embeddings, puntaje, RAG con Ollama
│   │   ├── db/               # modelos SQL y migraciones
│   │   └── api/              # FastAPI
│   └── tests/
├── data/
│   ├── skills_taxonomy.yaml
│   ├── labeled/              # vacantes etiquetadas a mano para evaluar
│   └── sample/               # muestra pequeña pública
├── notebooks/
│   ├── 01_eda.ipynb
│   ├── 02_skill_extraction_eval.ipynb
│   └── 03_match_eval.ipynb
├── frontend/                 # TypeScript
└── docs/architecture.md
```

## Comandos

> Se completan en la Fase 0. Mantener esta sección actualizada.

```bash
docker compose up -d db                 # levantar Postgres + pgvector
cd backend && uv sync                   # instalar dependencias
uv run pre-commit install               # una vez: ruff corre en cada commit
uv run ruff check . && uv run ruff format --check .
uv run pytest
uv run python -m jobmatch.ingest        # correr la ingesta
uv run uvicorn jobmatch.api.main:app --reload
cd frontend && npm install && npm run dev
```

## Fases (trabajar en orden; un PR por fase)

- [x] **Fase 0 — Base del repo:** `uv`, `ruff`, `pre-commit`, `pytest`, `docker-compose.yml`, CI en GitHub Actions, README inicial.
- [ ] **Fase 1 — Ingesta:** cliente de Remotive y luego Adzuna con modelos `pydantic`; JSON crudo + tabla `jobs` normalizada; deduplicar; cargar un dataset de Kaggle; tests con fixtures grabados.
- [ ] **Fase 2 — Limpieza y EDA:** normalizar salarios (anual, USD/MXN), clasificar seniority, notebook de EDA, reporte de calidad de datos.
- [ ] **Fase 3 — Skills con NLP:** taxonomía (~150 skills con sinónimos), extractor con `PhraseMatcher`, 100 vacantes etiquetadas, medir precisión/recall/F1, mejorar con embeddings o NER y comparar contra la línea base.
- [ ] **Fase 4 — Dashboard:** FastAPI (`/stats/skills`, `/stats/salaries`, `/jobs`), frontend TypeScript, cron diario, deploy en Vercel con datos agregados.
- [ ] **Fase 5 — Match CV vs. vacante (RAG):** CV con Docling, embeddings en pgvector, puntaje híbrido (cobertura de skills + similitud), explicación con Ollama citando la vacante, lista de brechas, evaluar con precision@10.
- [ ] **Fase 6 — Pulido:** README con capturas/GIF y métricas reales, limitaciones, artículo corto.

## Reglas de datos (obligatorias)

- Solo APIs oficiales y datasets con licencia abierta: Remotive, Adzuna, Arbeitnow, USAJOBS, HN "Who is hiring?" (Algolia), Kaggle.
- **Nunca** hacer scraping de LinkedIn, Indeed, OCC ni Glassdoor.
- Guardar la fuente y la URL de cada vacante, y mostrarlas en el dashboard.
- Respetar límites de llamadas: caché local y reintentos con espera exponencial.
- No guardar datos personales de reclutadores (nombres, correos).
- Claves en `.env` (ignorado por git); solo `.env.example` en el repo.
- No subir datos crudos completos ni el CV real; usar `data/sample/` y un CV de ejemplo.

## Convenciones de código

- Python con type hints en todo; modelos de datos con `pydantic`.
- Funciones pequeñas y puras en `transform/` y `nlp/` para que sean fáciles de testear.
- Cada módulo nuevo llega con tests; las llamadas HTTP se prueban con fixtures, nunca contra la API real en CI.
- Toda mejora de un modelo se compara contra una línea base con métricas (no "parece que funciona mejor").
- Notebooks solo para exploración y evaluación; la lógica reutilizable vive en `src/jobmatch/`.
- Commits pequeños y descriptivos en inglés (`feat:`, `fix:`, `test:`, `docs:`).

## Cómo debe trabajar Claude aquí

- El usuario está aprendiendo ciencia de datos: explica brevemente el *por qué* de cada decisión técnica.
- Avanza una fase a la vez y marca las tareas completadas en esta lista.
- Antes de cambiar el stack o la estructura, pregunta.
- Corre `ruff` y `pytest` antes de dar algo por terminado.
- Relación con el libro *RAG with Python Cookbook*: la Fase 5 aplica sus recetas de chunking, embeddings, recuperación híbrida y evaluación de RAG.
