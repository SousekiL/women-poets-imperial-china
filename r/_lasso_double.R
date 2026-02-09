# 1. 对 social_degree 做 double LASSO
# 首先准备数据：treatment variable (social_degree) 和 outcome (is_bieji)
treatment1 <- X[, "social_degree"]
outcome <- y

# 准备控制变量（除去social_degree）
controls1 <- X[, !colnames(X) %in% c("social_degree")]

# Step 1: LASSO regression of treatment on controls
set.seed(480)
lasso_treat1 <- cv.glmnet(controls1, treatment1,
                          alpha = 1,
                          nfolds = 10)

# Step 2: LASSO regression of outcome on controls
set.seed(480)
lasso_outcome1 <- cv.glmnet(controls1, outcome,
                            alpha = 1,
                            family = "binomial",
                            nfolds = 10)

# 获取选中的变量
selected_vars1_treat <- which(coef(lasso_treat1, s = "lambda.min")[-1] != 0)
selected_vars1_outcome <- which(coef(lasso_outcome1, s = "lambda.min")[-1] != 0)
selected_vars1 <- unique(c(selected_vars1_treat, selected_vars1_outcome))

# 使用选中的控制变量进行最终回归
selected_controls1 <- controls1[, selected_vars1]
final_data1 <- data.frame(
  outcome = outcome,
  treatment = treatment1,
  selected_controls1
)

# 最终回归获取处理效应
final_model1 <- glm(outcome ~ ., data = final_data1, family = "binomial")
social_effect <- coef(final_model1)["treatment"]

# 2. 对 kinship_degree 做 double LASSO
# 准备数据
treatment2 <- X[, "kinship_degree"]
# 准备控制变量（除去kinship_degree）
controls2 <- X[, !colnames(X) %in% c("kinship_degree")]

# Step 1: LASSO regression of treatment on controls
set.seed(480)
lasso_treat2 <- cv.glmnet(controls2, treatment2,
                          alpha = 1,
                          nfolds = 10)

# Step 2: LASSO regression of outcome on controls
set.seed(480)
lasso_outcome2 <- cv.glmnet(controls2, outcome,
                            alpha = 1,
                            family = "binomial",
                            nfolds = 10)

# 获取选中的变量
selected_vars2_treat <- which(coef(lasso_treat2, s = "lambda.min")[-1] != 0)
selected_vars2_outcome <- which(coef(lasso_outcome2, s = "lambda.min")[-1] != 0)
selected_vars2 <- unique(c(selected_vars2_treat, selected_vars2_outcome))

# 使用选中的控制变量进行最终回归
selected_controls2 <- controls2[, selected_vars2]
final_data2 <- data.frame(
  outcome = outcome,
  treatment = treatment2,
  selected_controls2
)

# 最终回归获取处理效应
final_model2 <- glm(outcome ~ ., data = final_data2, family = "binomial")
kinship_effect <- coef(final_model2)["treatment"]

# 输出结果
results <- data.frame(
  Variable = c("Social Degree", "Kinship Degree"),
  Effect = c(social_effect, kinship_effect)
)


# 可以进一步分析选中的控制变量
social_controls <- colnames(controls1)[selected_vars1]
kinship_controls <- colnames(controls2)[selected_vars2]

# 如果需要，还可以计算标准误和置信区间
social_se <- sqrt(vcov(final_model1)["treatment", "treatment"])
kinship_se <- sqrt(vcov(final_model2)["treatment", "treatment"])

results_with_ci <- data.frame(
  Variable = c("Social Degree", "Kinship Degree"),
  Effect = c(social_effect, kinship_effect),
  SE = c(social_se, kinship_se),
  CI_lower = c(social_effect - 1.96*social_se, kinship_effect - 1.96*kinship_se),
  CI_upper = c(social_effect + 1.96*social_se, kinship_effect + 1.96*kinship_se)
)


# 生成表格
# 首先整理数据，美化数值的显示格式
results_table <- results_with_ci %>%
  mutate(
    Effect = sprintf("%.3f", Effect),
    SE = sprintf("%.3f", SE),
    CI = sprintf("[%.3f, %.3f]", CI_lower, CI_upper)
  ) %>%
  select(Variable, Effect, SE, CI)  # 重新组织列

# 使用kable生成表格
kable(results_table, 
      caption = "Double LASSO Treatment Effects",
      col.names = c("Network Type", "Coefficient", "Std. Error", "95% CI")) %>%
  kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"),
                full_width = TRUE) %>%
  column_spec(1, bold = TRUE, width = "10em") %>%
  column_spec(2:3, width = "6em") %>%
  column_spec(4, width = "10em") %>%
  row_spec(0, bold = TRUE) %>%
  footnote(
    general = "Estimates from Double LASSO regression controlling for dynasty, region, and status variables.",
    number = c("Social Degree shows a significant positive effect",
               "Kinship Degree shows a positive but non-significant effect")
  )