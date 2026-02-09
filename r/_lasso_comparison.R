
#===============================#
# Data Clean ====
#===============================#

df.wide.kin <- df.poet.networks.unique %>%
  select(from, to_name, type) %>%
  unique() %>%
  group_by(from, to_name) %>%
  summarise(type = sum(type)) %>%
  ungroup() %>%
  filter(type %in% c(1,3)) %>% # kinship + both
  select(-type) %>%
  unique() %>%
  mutate(value = 1) %>%
  dcast(from ~ to_name, value.var = "value", fill = 0)

df.wide.social <- df.poet.networks.unique %>%
  select(from, to_name, type) %>%
  unique() %>%
  group_by(from, to_name) %>%
  summarise(type = sum(type)) %>%
  ungroup() %>%
  filter(type == 2) %>%
  mutate(value = 1) %>%
  dcast(from ~ to_name, value.var = "value", fill = 0)

df.wide.both <- df.poet.networks.unique %>%
  select(from, to_name, type) %>%
  unique() %>%
  group_by(from, to_name) %>%
  summarise(type = sum(type)) %>%
  ungroup() %>%
  filter(type == 3) %>%
  mutate(value = 1) %>%
  dcast(from ~ to_name, value.var = "value", fill = 0)

df.wide.dynasty <- df.poet.dynasty %>%
  dplyr::select(c_personid, c_dynasty) %>%
  mutate(value = 1) %>%       
  dcast(c_personid ~ c_dynasty, value.var = "value", fill = 0) 

df.wide.province <- df.poet.province %>%
  mutate(value = 1) %>%       
  dcast(c_personid ~ ENG_NAME, value.var = "value", fill = 0)

#===============================#
# Data Merge                ====
#===============================#

# 2. 合并数据并准备LASSO分析
# 为了区分两种关系，给列名加前缀
df.wide.kin <- df.wide.kin %>%
  rename_with(~ paste0("kin.", .),
    .cols = -c(from)
  )
df.wide.social <- df.wide.social %>%
  rename_with(~ paste0("social.", .),
    .cols = -c(from)
  )
df.wide.both <- df.wide.both %>%
  rename_with(~ paste0("both.", .),
    .cols = -c(from)
  )
df.wide.dynasty <- df.wide.dynasty %>%
  # reference
  dplyr::select(-Tang) %>%
  rename_with(~ paste0("dynasty.", .),
              .cols = -c(c_personid)
  )

df.wide.province <- df.wide.province %>%
  # reference
  dplyr::select(-Shandong) %>%
  rename_with(~ paste0("region.", .),
              .cols = -c(c_personid)
  )

# Data merge 
df.combined <- df.wide.kin %>%
  
  ## networks data ----
  left_join(df.wide.social, by = "from") %>%
  # left_join(df.wide.both, by = "from") %>%
  
  ## other predictors ----
  ### dynasities ----
  left_join(df.wide.dynasty, 
            by = c("from" = "c_personid")) %>%
  ### jinshi_cout ----
  left_join(select(poets_buff_summary_results, poet_personid, jinshi_count),
            by = c("from" = "poet_personid")) %>%
  rename_with(~ paste0("region.", .),
              .cols = c(jinshi_count)) %>%
  ### province ----
  left_join(df.wide.province,
            by = c("from" = "c_personid")) %>%
  ### socialeconomic status ----
  left_join(df.poet.kin.quality,
            by = c("from" = "c_personid")) %>%
  # y
  left_join(select(df.wide, from, is_bieji), by = "from")

df.combined[is.na(df.combined)] <- 0

#===============================#
# Run LASSO Model ====
#===============================#
library(glmnet)
X <- as.matrix(df.combined %>%
  select(-from, -is_bieji))
X[is.na(X)] <- 0
y <- df.combined$is_bieji
set.seed(480)
lasso_fit <- cv.glmnet(X, y,
  alpha = 1,
  family = "binomial",
  nfolds = 10
)

#===============================#
# Comparison Two Networks ====
#===============================#

# 4. 分析结果
# 获取系数并分别统计两种关系的影响
coef_df <- coef(lasso_fit, s = "lambda.min") %>%
  as.matrix() %>%
  as.data.frame() %>%
  rownames_to_column("variable") %>%
  filter(abs(s1) > 0, variable != "(Intercept)") # 只保留非零系数

# 分别统计两种关系的影响
kin_effects <- coef_df %>%
  filter(grepl("kin.", variable)) %>%
  summarise(
    n_vars = n(),
    mean_coef = mean(abs(s1)),
    sum_coef = sum(abs(s1))
  )

social_effects <- coef_df %>%
  filter(grepl("social.", variable)) %>%
  summarise(
    n_vars = n(),
    mean_coef = mean(abs(s1)),
    sum_coef = sum(abs(s1))
  )

both_effects <- coef_df %>%
  filter(grepl("both.", variable)) %>%
  summarise(
    n_vars = n(),
    mean_coef = mean(abs(s1)),
    sum_coef = sum(abs(s1))
  )


#===============================#
# violin plot ====
#===============================#

p1 <- coef_df %>%
  mutate(
    relation_type = case_when(
      startsWith(variable, "kin") ~ "Kinship",
      startsWith(variable, "social") ~ "Social Relations",
      startsWith(variable, "both") ~ "Both Relations",
      startsWith(variable, "dynasty") ~ "Dynasty",
      startsWith(variable, "region") ~ "Region",
      startsWith(variable, "status") ~ "Social Status",
      TRUE ~ "Other Predictors"
    ),
    relation_type = factor(relation_type, levels = c("Kinship", "Social Relations", "Both Relations", 
                                                     "Dynasty", "Region", "Social Status"))
  ) %>%
  group_by(relation_type) %>%
  mutate(
    positive_prop = mean(s1 > 0) * 100,
    max_y = max(s1) + 0.1 * diff(range(s1))
  ) %>%
  ggplot(aes(x = relation_type, y = s1)) +
  # 替换 geom_violin 为 geom_boxplot
  geom_boxplot(fill = "lightgray", width = 0.7) +
  geom_jitter(aes(color = s1 > 0), width = 0.2, size = 3, alpha = 0.7) +
  geom_hline(yintercept = 0, linetype = "dashed") +
  # 添加均值点
  stat_summary(fun = mean, geom = "point", size = 3, aes(shape = "Mean"), color = "black") +
  scale_color_manual(values = c("FALSE" = "darkblue", "TRUE" = "darkred")) +
  scale_shape_manual(values = c("Mean" = 19)) +
  theme_common() +
  stat_summary(
    fun.data = function(x) {
      data.frame(
        y = 2.5,
        label = sprintf("Mean: %.3f", mean(x))
      )
    },
    geom = "label",
    color = "black",
    fill = "white",
    label.padding = unit(0.5, "lines"),
    label.size = 0.5,
    size = 5
  ) +
  coord_cartesian(clip = "off") +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.10))) + 
  labs(
    title = "Distribution of LASSO Coefficients by Predictor Type",
    subtitle = "Showing positive and negative effects",
    x = "Type of Predictors",
    y = "Coefficient Value",
    color = "Positive Effect",
    shape = ""
  ) +
  guides(
    color = guide_legend(order = 1),
    shape = guide_legend(order = 2)
  )


p2 <- coef_df %>%
  mutate(
    relation_type = case_when(
      startsWith(variable, "kin") ~ "Kinship",
      startsWith(variable, "social") ~ "Social Relations",
      startsWith(variable, "both") ~ "Both Relations",
      startsWith(variable, "dynasty") ~ "Dynasty",
      startsWith(variable, "region") ~ "Region",
      startsWith(variable, "status") ~ "Social Status",
      TRUE ~ "Other Predictors"
    ),
    relation_type = factor(relation_type, levels = c("Kinship", "Social Relations", "Both Relations", 
                                                     "Dynasty", "Region", "Social Status"))
  ) %>%
  group_by(relation_type) %>%
  mutate(
    positive_prop = mean(s1 > 0) * 100,
    max_y = max(s1) + 0.1 * diff(range(s1))
  ) %>%
  ggplot(aes(x = relation_type, y = s1)) +
  geom_violin(fill = "lightgray") +
  geom_jitter(aes(color = s1 > 0), width = 0.2, size = 3, alpha = 0.7) +
  geom_hline(yintercept = 0, linetype = "dashed") +
  # 添加均值点并设置形状，加入新的aes映射
  stat_summary(fun = mean, geom = "point", size = 3, aes(shape = "Mean"), color = "black") +
  scale_color_manual(values = c("FALSE" = "darkblue", "TRUE" = "darkred")) +
  # 添加形状的scale
  scale_shape_manual(values = c("Mean" = 19)) +
  theme_common() +
  stat_summary(
    fun.data = function(x) {
      data.frame(
        y = 2.5,
        label = sprintf("Mean: %.3f", mean(x))
      )
    },
    geom = "label",
    color = "black",
    fill = "white",
    label.padding = unit(0.5, "lines"),
    label.size = 0.5,
    size = 5
  ) +
  coord_cartesian(clip = "off") +
  scale_y_continuous(expand = expansion(mult = c(0.05, 0.10))) + 
  labs(
    title = "Distribution of LASSO Coefficients by Predictor Type",
    subtitle = "Showing positive and negative effects",
    x = "Type of Predictors",
    y = "Coefficient Value",
    color = "Positive Effect",
    shape = "" # 设置shape图例的标题为空
  ) +
  guides(
    color = guide_legend(order = 1),
    shape = guide_legend(order = 2)
  )


print(p1)
