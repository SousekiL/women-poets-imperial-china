### Growing in the Margins of Men’s Narration

**Article**: *Growing in the Margins of Men’s Narration: How Women Poets Claimed Literary Recognition in Imperial China*  
**Author**: Weifeng Liu  
**Source file**: `output/Liu_Poets_Jul29.pdf`

### Research Focus

The paper examines how women poets in imperial China secured **literary recognition** in a highly patriarchal system where they lacked formal institutional power. It argues that women managed professional risks not mainly through inherited family status, but through **social capital embedded in networks of relationships**, especially with male elites beyond the household.

The key outcome is whether a woman poet published at least one **individual poetry collection (bieji/別集)**, treated as a strong indicator of professional recognition compared to inclusion only in anthologies.

### Data and Methods

- **Data sources**
  - **China Biographical Database (CBDB)**: large-scale biographical and relationship data (7th–19th centuries), used to reconstruct kinship and social ties.
  - **Ming Qing Women’s Writings (MQWW)**: corpus of women’s writings, used to identify women poets and their publication records.
- **Operationalization of social capital**
  - **Kinship networks**: ascending, descending, affinal, and collateral relatives.
  - **Social (non-kin) networks**: academic ties, political connections, patronage, literary and artistic exchange, correspondence, service, and economic ties.
- **Outcome variable**
  - Binary indicator of whether a woman poet has at least one individual collection (`bieji > 0`).
- **Statistical strategy**
  - **LASSO regression** on high-dimensional data (\(n = 443, p = 1391\)) to select important predictors and estimate effects of **kinship degree** and **social degree** (network centrality measures).
  - **Double LASSO** to obtain more credible treatment effects by separating the effect of social capital from other correlated controls (dynasty, region, status).
  - **Bayesian hierarchical logistic model** with dynasty-level random intercepts, estimating posterior distributions for kinship degree, social degree, and dynastic variation in baseline recognition.

### Main Empirical Findings

- **Non-kin social networks are more influential than kinship networks.**
  - In the LASSO model, the coefficient for **social degree** (\(\approx 0.223\)) is larger than that for **kinship degree** (\(\approx 0.102\)), indicating stronger association between broad social ties and women’s literary recognition.
  - Double LASSO shows that, once other predictors are controlled, the effect of **kinship degree** effectively disappears (estimate ≈ 0), while **social degree** remains robustly positive (≈ 0.211).
- **Bootstrap inference confirms the centrality of social ties.**
  - With 500 bootstrap replications, the estimated effect of **social degree** is about **0.287** with a 95% confidence interval that excludes zero, while the effect of **kinship degree** is statistically insignificant.
  - Substantively, a one-unit increase in social degree raises the odds of a woman poet having an individual collection by roughly **25%**.
- **Bayesian analysis strengthens the conclusions.**
  - The posterior mean for **social degree** is about **0.724** (95% credible interval [0.296, 1.203]), implying that a one standard-deviation increase in social degree roughly **doubles the odds** of publishing an individual collection \(\big(\exp(0.724) \approx 2.06\big)\).
  - The posterior mean for **kinship degree** is modest (≈ 0.226) and its credible interval crosses zero, indicating **no clear evidence** that kinship networks independently drive recognition.
  - The estimated standard deviation of dynasty-level random intercepts is large, indicating **substantial historical variation**: some dynasties structurally offered better baseline opportunities for women’s recognition than others.

### Interpretation and Theoretical Implications

- **Gendered social capital**:
  - Classic work on Chinese history emphasizes the power of **lineage and kinship** for male mobility in examinations, bureaucracy, and commerce.
  - This study shows that **for women poets**, kinship alone was not enough. What mattered most was **actively built, non-kin social networks**—academic exchange, literary circles, artistic collaborations, and political or patronage links.
- **Managing professional risk through networks**:
  - Without formal offices or examinations, women’s literary careers were fragile and exposed to social and reputational risks.
  - By positioning themselves at the **center of diverse social networks**, women could:
    - Circulate their writings more widely,
    - Attract influential readers and sponsors,
    - Gain invitations to anthologies and, crucially, support for **individual collections**.
- **Contribution to social capital theory**:
  - The findings refine Western theories (e.g. Bourdieu, Granovetter, Burt) in a non-Western, historical, and strongly patriarchal context.
  - They highlight a **gendered divergence** in how social capital operates: for women, **non-kin ties** are especially important vehicles for converting social connection into professional achievement.

### Key Figures from the Paper

- **LASSO results for kinship vs. social networks**  
  ![LASSO coefficients for kinship and social degree predictors](output/images/fig-lasso.pdf)

- **Network structures of women poets and male elites**  
  ![Kinship and social network structures linking women poets to male elites](output/images/fig-jinshi.pdf)

