# CLAUDE.md

## Project Overview

Academic research project: "Growing in the Margins of Men's Narration: How Women Poets Claimed Literary Recognition in Imperial China" by Liu, Weifeng. Analyzes women poets' literary recognition using network analysis, LASSO regression, Bayesian inference, and random forest modeling. Data sourced from CBDB and MQWW.

## Tech Stack

- **R** (4.0+): Data analysis and statistical modeling
- **Quarto**: Reproducible research documents (`.qmd` files)
- **SQLite**: Database interaction with CBDB via `DBI`/`RSQLite`

## Project Structure

```
index.qmd          # Main document (renders to HTML)
_quarto.yml        # Quarto project configuration
data/              # CSV datasets and serialized R data objects (.Rda)
r/                 # R analysis scripts (prefixed with _ for helpers)
output/            # Generated results
  images/          # Generated figures (PDF, TIFF, PNG)
  tables/          # Generated LaTeX tables (tbl_*.tex)
style/             # Bibliography, citation styles, CSS
```

## Build / Render

```bash
quarto render index.qmd
```

## Configuration

External data paths are configured via environment variables (defaults in `index.qmd` setup chunk):

- `CBDB_DB_PATH` - Path to CBDB SQLite database
- `MQWW_POEM_PATH` - Path to MQWW poem CSV
- `CANGER_FONT` - Path to CJK font file (optional)

## R Script Conventions

- Helper/utility scripts are prefixed with underscore: `_theme.R`, `_cbdb_read.R`
- Main analysis scripts use descriptive names: `Bayesian.R`, `kin_clean.R`
- Section dividers use `#===` and `#---` comment blocks
- Comments mix English and Chinese

## Dependencies

R packages: `tidyverse`, `ggplot2`, `DBI`, `RSQLite`, `data.table`, `glmnet`, `gamlr`, `rjags`, `coda`, `bayesplot`, `igraph`, `ggraph`, `sf`, `showtext`, `kableExtra`, `patchwork`, `gridExtra`

## Notes

- No automated test suite or linter configured
- No CI/CD pipeline
- CJK font (Canger) is optional; `showtext` handles font loading gracefully
