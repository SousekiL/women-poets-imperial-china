# CLAUDE.md

## Project Overview

Academic research project: "Growing in the Margins of Men's Narration: How Women Poets Claimed Literary Recognition in Imperial China" by Liu, Weifeng. Analyzes women poets' literary recognition using network analysis, LASSO regression, Bayesian inference, and random forest modeling. Data sourced from CBDB (China Biographical Database).

## Tech Stack

- **R** (4.0+): Data analysis and statistical modeling
- **Quarto**: Reproducible research documents (`.qmd` files)
- **LaTeX/XeLaTeX**: PDF generation with CJK font support
- **SQLite**: Database interaction with CBDB via `DBI`/`RSQLite`

## Project Structure

```
data/           # CSV datasets and serialized R data objects (.Rda)
r/              # R analysis scripts (prefixed with _ for helpers/utilities)
output/         # Generated PDFs, presentations, LaTeX tables, figures
  images/       # Generated figures (PDF, TIFF, PNG)
  tables/       # Generated LaTeX tables (tbl_*.tex)
style/          # BibTeX bibliography and CSL citation styles
```

## Key Files

- `ASRM539_Final_for_DSH.qmd` - Main research paper (Quarto)
- `Literature_Html_for_Github.qmd` - Literature review (HTML output)
- `style/womenreference.bib` - Bibliography database

## Build Commands

```bash
# Render the main paper
quarto render ASRM539_Final_for_DSH.qmd

# Render the literature review
quarto render Literature_Html_for_Github.qmd
```

## R Script Conventions

- Helper/utility scripts are prefixed with underscore: `_theme.R`, `_cbdb_read.R`
- Main analysis scripts use descriptive names: `Bayesian.R`, `kin_clean.R`
- Section dividers use `#===` and `#---` comment blocks
- Comments mix English and Chinese

## Dependencies

R packages: `rjags`, `coda`, `bayesplot`, `gamlr`, `dplyr`, `tidyverse`, `data.table`, `ggplot2`, `gridExtra`, `showtext`, `DBI`, `RSQLite`, `kableExtra`, `knitr`, `magrittr`

System: XeLaTeX with CJK fonts (STSong, Charter)

## Notes

- No automated test suite or linter configured
- No CI/CD pipeline
- Chinese text rendering requires CJK font support (`showtext` package with "Canger" font in ggplot2 theme)
