library(parallel)

# 设置随机种子
set.seed(480)

# 设置bootstrap参数
B <- 500  # bootstrap重复次数

# 创建并行集群
cl <- makeCluster(detectCores())

# 导出需要的对象和包到集群
# 对social_degree的分析
clusterExport(cl, c("X_control1", "d1", "y"))
clusterEvalQ(cl, library(gamlr))

# 定义bootstrap函数 - social_degree
boot_function_social <- function(ib) {
  # 拟合第一阶段
  first_stage <- gamlr(X_control1[ib,], d1[ib])
  dhat1 <- drop(predict(first_stage, X_control1[ib,]))
  
  # Double LASSO回归
  social_dlasso <- gamlr(cbind(d1[ib], dhat1, X_control1[ib,]),
                         y=y[ib],
                         free=2,
                         family="binomial")
  
  return(coef(social_dlasso)[2])
}

# 生成重抽样索引
n <- nrow(X)
resamp <- as.data.frame(matrix(sample(1:n, B*n, replace=TRUE), ncol=B))

# 运行并行bootstrap - social_degree
d1_samp <- unlist(parLapply(cl, resamp, boot_function_social))

# 对kinship_degree的分析
clusterExport(cl, c("X_control2", "d2"))

# 定义bootstrap函数 - kinship_degree
boot_function_kinship <- function(ib) {
  # 拟合第一阶段
  first_stage <- gamlr(X_control2[ib,], d2[ib])
  dhat2 <- drop(predict(first_stage, X_control2[ib,]))
  
  # Double LASSO回归
  kinship_dlasso <- gamlr(cbind(d2[ib], dhat2, X_control2[ib,]),
                          y=y[ib],
                          free=2,
                          family="binomial")
  
  return(coef(kinship_dlasso)[2])
}

# 运行并行bootstrap - kinship_degree
d2_samp <- unlist(parLapply(cl, resamp, boot_function_kinship))

# 关闭集群
stopCluster(cl)

# 计算估计值和标准误
results_boot <- data.frame(
  Variable = c("Social Degree", "Kinship Degree"),
  Estimate = c(mean(d1_samp, na.rm=TRUE), mean(d2_samp, na.rm=TRUE)),
  Std_Error = c(sd(d1_samp, na.rm=TRUE), sd(d2_samp, na.rm=TRUE))
)

results_boot <- results_boot %>%
  mutate(
    CI_lower = Estimate - 1.96 * Std_Error,
    CI_upper = Estimate + 1.96 * Std_Error
  )

# 可视化结果
# 打开 PDF 设备
pdf("output/images/bootstrap-dist.pdf",   # 文件路径和名称
    width = 12,                  # 宽度（英寸）
    height = 6) 

par(mfrow=c(1,2))

# Social Degree
hist(d1_samp, 
     main="Bootstrap Distribution: Social Degree",
     xlab="Estimated Effect",
     breaks=30,
     col="lightblue",
     border="white")
abline(v=results_boot$Estimate[1], col="red", lwd=2)
abline(v=c(results_boot$CI_lower[1], results_boot$CI_upper[1]), 
       col="blue", lty=2)

# plot(density(d1_samp, na.rm=TRUE),
#      main="Density Plot: Social Degree",
#      xlab="Estimated Effect")
# abline(v=results_boot$Estimate[1], col="red", lwd=2)
# abline(v=c(results_boot$CI_lower[1], results_boot$CI_upper[1]), 
#        col="blue", lty=2)

# Kinship Degree
hist(d2_samp, 
     main="Bootstrap Distribution: Kinship Degree",
     xlab="Estimated Effect",
     breaks=30,
     col="darkorange",
     border="white")
abline(v=results_boot$Estimate[2], col="red", lwd=2)
abline(v=c(results_boot$CI_lower[2], results_boot$CI_upper[2]), 
       col="blue", lty=2)

dev.off()
# plot(density(d2_samp, na.rm=TRUE),
#      main="Density Plot: Kinship Degree",
#      xlab="Estimated Effect")
# abline(v=results_boot$Estimate[2], col="red", lwd=2)
# abline(v=c(results_boot$CI_lower[2], results_boot$CI_upper[2]), 
#        col="blue", lty=2)

# # 使用kable展示结果
# kable(results_boot %>%
#         mutate(
#           Estimate = sprintf("%.3f", Estimate),
#           Std_Error = sprintf("%.3f", Std_Error),
#           CI = sprintf("[%.3f, %.3f]", CI_lower, CI_upper)
#         ) %>%
#         select(Variable, Estimate, Std_Error, CI),
#       caption = "Double LASSO Treatment Effects (Bootstrap)",
#       col.names = c("Network Type", "Estimate", "Std. Error", "95% CI")) %>%
#   kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"),
#                 full_width = FALSE) %>%
#   footnote(
#     general = paste("Based on", B, "bootstrap replications"),
#     number = c(
#       "Parallel processing using all available cores",
#       "Bootstrap samples with replacement"
#     )
#   )

# # 打印诊断信息
# cat("
# Bootstrap Diagnostics:
# ")
# cat("
# Social Degree:")
# cat("
# Number of NA/failed estimates:", sum(is.na(d1_samp)))
# cat("
# Proportion of successful estimates:", mean(!is.na(d1_samp)))
# cat("
# 95% CI: [", results_boot$CI_lower[1], ",", results_boot$CI_upper[1], "]
# ")
# 
# cat("
# Kinship Degree:")
# cat("
# Number of NA/failed estimates:", sum(is.na(d2_samp)))
# cat("
# Proportion of successful estimates:", mean(!is.na(d2_samp)))
# cat("
# 95% CI: [", results_boot$CI_lower[2], ",", results_boot$CI_upper[2], "]
# ")
