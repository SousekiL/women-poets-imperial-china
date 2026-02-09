library(gamlr)
# 准备数据
# 1. 对social_degree的分析
# 创建处理变量
d1 <- X[, "social_degree"]

# 第一阶段：对treatment进行LASSO回归得到预测值
X_control1 <- X[, !colnames(X) %in% c("social_degree")]
first_stage1 <- gamlr(X_control1, y=d1)
dhat1 <- predict(first_stage1, X_control1, type="response")

# Double LASSO回归
social_dlasso <- gamlr(cbind(d1, dhat1, X_control1), 
                       y=y, 
                       family="binomial",
                       free=2)  # free=2表示前两个变量(d和dhat)不被惩罚

# 2. 对kinship_degree的分析
# 创建处理变量
d2 <- X[, "kinship_degree"]

# 第一阶段：对treatment进行LASSO回归得到预测值
X_control2 <- X[, !colnames(X) %in% c("kinship_degree")]
first_stage2 <- gamlr(X_control2, y=d2)
dhat2 <- predict(first_stage2, X_control2, type="response")

# Double LASSO回归
kinship_dlasso <- gamlr(cbind(d2, dhat2, X_control2), 
                        y=y, 
                        family="binomial",
                        free=2)

# 提取结果
# 对social_degree
social_coef <- coef(social_dlasso)[2]  # 第二个系数是dhat的系数
# social_se <- sqrt(vcov(social_dlasso)[2,2])

# 对kinship_degree
kinship_coef <- coef(kinship_dlasso)[2]
# kinship_se <- sqrt(vcov(kinship_dlasso)[2,2])

# 整理结果
results_dlasso <- data.frame(
  Variable = c("Social Degree", "Kinship Degree"),
  Coefficient = c(social_coef, kinship_coef)
  # Std_Error = c(social_se, kinship_se),
  # CI_lower = c(social_coef - 1.96*social_se, kinship_coef - 1.96*kinship_se),
  # CI_upper = c(social_coef + 1.96*social_se, kinship_coef + 1.96*kinship_se)
)

# # 使用kable展示结果
# kable(results_dlasso %>%
#         mutate(
#           Coefficient = sprintf("%.3f", Coefficient),
#           Std_Error = sprintf("%.3f", Std_Error),
#           CI = sprintf("[%.3f, %.3f]", CI_lower, CI_upper)
#         ) %>%
#         select(Variable, Coefficient, Std_Error, CI),
#       caption = "Double LASSO Treatment Effects (using gamlr)",
#       col.names = c("Network Type", "Coefficient", "Std. Error", "95% CI")) %>%
#   kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"),
#                 full_width = TRUE) %>%
#   column_spec(1, bold = TRUE, width = "15em") %>%
#   column_spec(2:4, width = "12em") %>%
#   row_spec(0, bold = TRUE) %>%
#   footnote(
#     general = "Note: Estimates from Double LASSO regression using gamlr package.",
#     number = c(
#       "Treatment variables (d and dhat) were not penalized in the estimation.",
#       "Controls include dynasty, region, and status variables."
#     )
#   )
# 
# # 可以添加选中的控制变量分析
# selected_controls_social <- which(coef(social_dlasso)[-c(1,2)] != 0)
# selected_controls_kinship <- which(coef(kinship_dlasso)[-c(1,2)] != 0)
