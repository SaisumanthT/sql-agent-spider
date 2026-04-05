# Portfolio Guide

This file gives you a clean step-by-step path to publish the project as a polished GitHub repo.

## 1. Verify the project runs locally

```powershell
python -m pytest -q
python scripts/setup_local_db.py
python scripts/run_demo.py --mode realistic --question "Which customers have never placed an order?"
streamlit run streamlit_app.py
```

Use the Streamlit app to capture one or two screenshots showing:

- the database preview
- an English question
- the generated SQL
- the final answer table

## 2. Run the benchmark script

```powershell
python scripts/run_benchmark.py --num-examples 25 --mode benchmark
```

The local retail question bank currently includes 6 seeded benchmark prompts, so the script will run those and write the output to `results/benchmark_report.csv`.

Review the CSV and note:

- how many benchmark questions succeeded
- average number of attempts
- common failure categories

## 3. Use a clean GitHub repo name

Recommended names:

- `retail-sql-agent`
- `text-to-sql-retail-agent`
- `ask-sql-retail`

## 4. Push the repo

If the folder is not already a git repo:

```powershell
git init
git add .
git commit -m "Initial retail SQL agent project"
```

Then create an empty GitHub repository and push:

```powershell
git remote add origin https://github.com/<your-username>/retail-sql-agent.git
git branch -M main
git push -u origin main
```

## 5. Add GitHub topics

Use:

- `text-to-sql`
- `llm-agents`
- `autogen`
- `sqlite`
- `streamlit`
- `sql`
- `python`
- `data-engineering`

## 6. Pin it on your profile

On GitHub:

1. Open your profile.
2. Click `Customize your pins`.
3. Pin the new retail SQL repo.

## 7. Resume version

Use something like this:

**Retail SQL Agent** | Python, AutoGen, SQLite, Streamlit, OpenAI API

- Built a text-to-SQL agent that converts natural-language analytics questions into executable SQL against a seeded retail database.
- Implemented a tool-driven retry loop that executes generated SQL, classifies failures, and improves queries using execution feedback.
- Delivered a Streamlit UI for database preview, plain-English querying, generated SQL inspection, and benchmark-style evaluation.

## 8. LinkedIn / portfolio summary

> Built a retail analytics text-to-SQL agent using Python, AutoGen, SQLite, and Streamlit. The system accepts plain-English questions, generates SQL, executes it against a local database, and retries when execution feedback shows the query needs correction.

## 9. Best next upgrade

If you want to make the project even stronger later, add a PostgreSQL version of the same schema and show that the same agent loop works beyond SQLite.
