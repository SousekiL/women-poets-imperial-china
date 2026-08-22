library(randomForest)

# 准备数据
rf_data <- df.combined %>%
  select(starts_with("kin"), 
         starts_with("social"),
         starts_with("dynasty"),
         starts_with("region"),
         starts_with("status"),
         is_bieji) %>%
  rename_all(make.names) %>%
  rename_with(~substr(., 1, 20), -matches("is_bieji"))

# 检查处理后的列名
colnames(rf_data)


# 运行随机森林
rf_model <- randomForest(factor(is_bieji) ~ ., 
                         data = rf_data,
                         importance = TRUE)

#===============================#
# importance ====
#===============================#

# 查看变量重要性
importance(rf_model)

# 可视化变量重要性
varImpPlot(rf_model, 
           main="Variable Importance in Random Forest Model",              # 移除主标题
           # pch=16,              # 点的样式
           # col=1:2,             # 两种指标的颜色
           cex=0.8)             # 点和文字的大小


# 准备数据
imp_df <- importance(rf_model) %>%
  as.data.frame() %>%
  rownames_to_column("variable") %>%
  mutate(
    relation_type = case_when(
      startsWith(variable, "kin") ~ "Kinship",
      startsWith(variable, "social") ~ "Social Relations",
      startsWith(variable, "both") ~ "Both Relations",
      startsWith(variable, "dynasty") ~ "Dynasty",
      startsWith(variable, "region") ~ "Region",
      startsWith(variable, "status") ~ "Social Status",
      TRUE ~ "Other Predictors"
    )
  )

# 准备Accuracy数据
acc_plot_data <- imp_df %>%
  select(variable, relation_type, MeanDecreaseAccuracy) %>%
  arrange(desc(MeanDecreaseAccuracy)) %>%
  slice_head(n = 25) %>%
  mutate(variable = factor(variable, levels = variable)) %>%
  arrange(MeanDecreaseAccuracy)

# 准备Gini数据
gini_plot_data <- imp_df %>%
  select(variable, relation_type, MeanDecreaseGini) %>%
  arrange(desc(MeanDecreaseGini)) %>%
  slice_head(n = 25) %>%
  mutate(variable = factor(variable, levels = variable)) %>%
  arrange(MeanDecreaseGini)

# 创建Accuracy图
p1 <- ggplot(acc_plot_data, 
             aes(x = variable, 
                 y = MeanDecreaseAccuracy,
                 color = relation_type)) +
  geom_point(size = 3) +
  geom_segment(aes(xend = variable, yend = 0), size = 0.7, alpha = 0.5) +
  coord_flip() +
  scale_color_brewer(palette = "Set2") +
  theme_minimal() +
  theme(
    legend.position = "none",  # 只在一个图中显示图例
    panel.grid.major.y = element_blank(),
    panel.grid.minor.y = element_blank(),
    axis.text = element_text(size = 9),
    plot.title = element_text(size = 12, face = "bold")
  ) +
  labs(
    title = "Mean Decrease in Accuracy",
    x = "",
    y = "Variable Importance"
  )

# 创建Gini图
p2 <- ggplot(gini_plot_data, 
             aes(x = variable, 
                 y = MeanDecreaseGini,
                 color = relation_type)) +
  geom_point(size = 3) +
  geom_segment(aes(xend = variable, yend = 0), size = 0.7, alpha = 0.5) +
  coord_flip() +
  scale_color_brewer(palette = "Set2") +
  theme_minimal() +
  theme(
    panel.grid.major.y = element_blank(),
    panel.grid.minor.y = element_blank(),
    axis.text = element_text(size = 9),
    plot.title = element_text(size = 12, face = "bold")
  ) +
  labs(
    title = "Mean Decrease in Gini",
    x = "",
    y = "Variable Importance",
    color = "Variable Type"
  )

# 使用grid.arrange拼接图形
library(gridExtra)
# grid.arrange(p1, p2, ncol = 2, widths = c(1, 1.5))  # 1.3是为了给右图留出图例的空间


#-------------------------------#
# 按类型汇总重要性 ----
#-------------------------------#

type_summary <- imp_df %>%
  group_by(relation_type) %>%
  summarise(
    mean_importance = mean(MeanDecreaseAccuracy),
    total_importance = sum(MeanDecreaseAccuracy),
    n_variables = n()
  ) %>%
  arrange(desc(mean_importance))

# 创建变量类型的总体重要性图
# ggplot(type_summary, 
#        aes(x = reorder(relation_type, mean_importance), 
#            y = mean_importance)) +
#   geom_bar(stat = "identity", fill = "steelblue") +
#   coord_flip() +
#   theme_minimal() +
#   labs(
#     title = "Average Variable Importance by Type",
#     x = "Variable Type",
#     y = "Mean Importance (Mean Decrease in Accuracy)"
#   )

# # 打印各类型的统计摘要
# print("Summary statistics by variable type:")
# print(type_summary)

# 找出每种类型中最重要的变量
top_by_type <- imp_df %>%
  group_by(relation_type) %>%
  slice_max(order_by = MeanDecreaseGini, n = 3) %>%
  arrange(relation_type, desc(MeanDecreaseGini))

# print("
# Top 3 most important variables by type:")
# print(top_by_type)

