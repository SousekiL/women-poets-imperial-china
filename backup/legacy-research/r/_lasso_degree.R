library(igraph)

# 构建网络
edges <- df.poet.networks.unique %>%
  filter(type %in% c(1,3)) %>%  # kinship relations
  select(from, to_name) %>%
  unique()

g <- graph_from_data_frame(edges, directed = TRUE)
network_kinship <- data.frame(
  person_id = V(g)$name,
  kinship_degree = degree(g)
  # betweenness = betweenness(g),
  # closeness = closeness(g),
  # eigen_centrality = eigen_centrality(g)$vector
)

edges <- df.poet.networks.unique %>%
  filter(type %in% c(2)) %>%  # kinship relations
  select(from, to_name) %>%
  unique()

g <- graph_from_data_frame(edges, directed = TRUE)
network_social <- data.frame(
  person_id = V(g)$name,
  social_degree = degree(g)
  # betweenness = betweenness(g),
  # closeness = closeness(g),
  # eigen_centrality = eigen_centrality(g)$vector
)

# 合并网络指标与原始数据
df_with_metrics <- df.combined %>%
  left_join(network_kinship, by = c("from" = "person_id")) %>%
  left_join(network_social, by = c("from" = "person_id"))

#-------------------------------#
# LASSO ----
#-------------------------------#


X <- as.matrix(df_with_metrics %>% 
                select(starts_with("dynasty."), 
                starts_with("region."), 
                starts_with("status."), 
                kinship_degree, social_degree))
X[is.na(X)] <- 0
y <- df.combined$is_bieji
set.seed(480)
lasso_fit_net <- cv.glmnet(X, y,
                       alpha = 1,
                       family = "binomial",
                       nfolds = 10
)


coef_df <- coef(lasso_fit_net, s = "lambda.min") %>%
  as.matrix() %>%
  as.data.frame() %>%
  rownames_to_column("variable") %>%
  filter(abs(s1) > 0, variable != "(Intercept)") # 只保留非零系数


# 首先创建汇总数据框
coef_df_summary <- coef_df %>%
  mutate(
    relation_type = case_when(
      startsWith(variable, "kinship_degree") ~ "Kinship Degree",
      startsWith(variable, "social_degree") ~ "Social Degree",
      startsWith(variable, "kin.") ~ "Kinship",
      startsWith(variable, "social.") ~ "Social Relations",
      startsWith(variable, "both") ~ "Both Relations",
      startsWith(variable, "dynasty") ~ "Dynasty",
      startsWith(variable, "region") ~ "Region",
      startsWith(variable, "status") ~ "Social Status",
      TRUE ~ "Other Predictors"
    ),
    relation_type = factor(relation_type, levels = c("Kinship Degree", "Social Degree",
                                                     "Kinship", "Social Relations", "Both Relations", 
                                                     "Dynasty", "Region", "Social Status"))
  ) %>%
  group_by(relation_type) %>%
  summarise(
    mean_coef = mean(s1),
    positive_prop = mean(s1 > 0) * 100,
    se = sd(s1) / sqrt(n())
  )

# 然后创建图形
p1 <- ggplot(coef_df_summary, aes(x = relation_type, y = mean_coef)) +
  geom_col(fill = "lightgray", width = 0.7) +
  geom_errorbar(aes(ymin = mean_coef - se, ymax = mean_coef + se), 
                width = 0.2) +
  geom_hline(yintercept = 0, linetype = "dashed") +
  geom_text(aes(label = sprintf("%.3f", mean_coef)), 
            vjust = ifelse(coef_df_summary$mean_coef >= 0, -0.5, 1.5),
            size = 5) +
  theme_common() +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.15))) + 
  labs(
    title = "Mean LASSO Coefficients by Predictor Type",
    subtitle = "With standard error bars",
    x = "Type of Predictors",
    y = "Mean Coefficient Value"
  ) 

# 显示图形
print(p1)

