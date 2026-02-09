# Women Poets in Imperial China

## Growing in the Margins of Men's Narration: How Women Poets Claimed Literary Recognition in Imperial China

This repository contains the research project and analysis for a study examining the literary contributions and recognition of women poets during Imperial China.

### Author

Liu, Weifeng (Felix Liu)

### Project Overview

This research explores how women poets navigated and claimed literary recognition within the male-dominated literary landscape of Imperial China. Using data from the China Biographical Database (CBDB) and Ming Qing Women's Writings (MQWW), the study employs LASSO regression, double LASSO, and Bayesian hierarchical models to analyze the role of social capital in women's literary success.

### Project Structure

```
.
├── index.qmd              # Main document (renders to HTML)
├── _quarto.yml            # Quarto project configuration
├── data/                  # Research datasets (.csv, .Rda)
├── r/                     # R analysis scripts
│   ├── _theme.R           #   ggplot2 theme customization
│   ├── _cbdb_read.R       #   CBDB data reading
│   ├── _cbdb_clean.R      #   CBDB data cleaning
│   ├── _cbdb_networks.R   #   Network construction
│   ├── _networks_degree.R #   Network degree analysis
│   ├── _plot_networks.R   #   Network visualization
│   ├── _lasso_*.R         #   LASSO regression variants
│   ├── _rf.R              #   Random forest analysis
│   ├── _get_jinshi.R      #   Jinshi examination data
│   ├── Bayesian.R         #   Bayesian statistical analysis
│   └── kin_clean.R        #   Kinship data cleaning
├── output/                # Generated results
│   ├── images/            #   Figures (PDF, TIFF, PNG)
│   └── tables/            #   LaTeX tables
└── style/                 # Bibliography and formatting
    ├── womenreference.bib #   BibTeX bibliography
    ├── custom.css         #   HTML styling
    └── *.csl              #   Citation style files
```

### Requirements

- R (4.0+)
- Quarto
- R packages: `tidyverse`, `ggplot2`, `DBI`, `RSQLite`, `data.table`, `glmnet`, `gamlr`, `rjags`, `coda`, `bayesplot`, `igraph`, `ggraph`, `sf`, `showtext`, `kableExtra`, `patchwork`

### Data Setup

This project requires external databases that are not included in the repository:

1. **CBDB database** - Download from [Harvard CBDB](https://projects.iq.harvard.edu/cbdb)
2. **MQWW poem data** - From the [Ming Qing Women's Writings](https://digital.library.mcgill.ca/mingqing/english/index.php) archive

Configure paths via environment variables or edit the defaults in `index.qmd`:

```bash
export CBDB_DB_PATH="/path/to/cbdb.db"
export MQWW_POEM_PATH="/path/to/mqww/poem.csv"
export CANGER_FONT="/path/to/font.ttf"  # optional CJK font
```

### Rendering

```bash
quarto render index.qmd
```

### License

This research is part of the ASRM539 course project.

### Contact

For questions or collaboration opportunities, please open an issue in this repository.
