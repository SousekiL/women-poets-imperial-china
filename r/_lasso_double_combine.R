# 整合三种方法的结果
compare_results <- data.frame(
  Method = c("Double LASSO", "OrthoLTE", "Bootstrap"),
  Social_Effect = c(social_coef,           # 常规方法
                    social_resids$gam,      # OrthoLTE
                    mean(d1_samp, na.rm=TRUE)), # Bootstrap
  Social_SE = c(social_se,                # 常规方法
                social_resids$se,         # OrthoLTE
                sd(d1_samp, na.rm=TRUE)), # Bootstrap
  Kinship_Effect = c(kinship_coef,          # 常规方法
                     kinship_resids$gam,     # OrthoLTE
                     mean(d2_samp, na.rm=TRUE)), # Bootstrap
  Kinship_SE = c(kinship_se,               # 常规方法
                 kinship_resids$se,        # OrthoLTE
                 sd(d2_samp, na.rm=TRUE))  # Bootstrap
)

# 添加置信区间
compare_results <- compare_results %>%
  mutate(
    Social_CI_lower = Social_Effect - 1.96 * Social_SE,
    Social_CI_upper = Social_Effect + 1.96 * Social_SE,
    Kinship_CI_lower = Kinship_Effect - 1.96 * Kinship_SE,
    Kinship_CI_upper = Kinship_Effect + 1.96 * Kinship_SE
  )


