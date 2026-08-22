library(sandwich)

# 定义正交估计函数
orthoLTE <- function(x, d, y, dreg, yreg, nfold=2){
  # randomly split data into folds
  nobs <- nrow(x)
  foldid <- rep.int(1:nfold, times=ceiling(nobs/nfold))[sample.int(nobs)]
  I <- split(1:nobs, foldid)
  
  # create residualized objects to fill
  ytil <- dtil <- rep(NA, nobs)
  
  # run the OOS orthogonalizations
  cat("fold: ")
  for(b in 1:length(I)){
    dfit <- dreg(x[- I[[b]], ], d[-I[[b]]])
    yfit <- yreg(x[- I[[b]], ], y[-I[[b]]])
    dhat <- predict(dfit, x[I[[b]], ], type="response") 
    yhat <- predict(yfit, x[I[[b]], ], type="response") 
    dtil[I[[b]]] <- drop(d[I[[b]]] - dhat)
    ytil[I[[b]]] <- drop(y[I[[b]]] - yhat)    
    cat(b," ")
  }
  
  rfit <- lm(ytil ~ dtil)
  gam <- coef(rfit)[2]
  se <- sqrt(vcovHC(rfit)[2,2])
  cat(sprintf("
gamma (se) = %g (%g)
", gam, se))
  
  return(list(gam=gam, se=se, dtil=dtil, ytil=ytil))
}

# 定义回归函数
dreg <- function(x, d){
  gamlr(x, d, lmr=1e-5, family="gaussian")  # 对连续变量用gaussian
}

yreg <- function(x, y){
  gamlr(x, y, lmr=1e-5, family="binomial")  # 对二元结果用binomial
}

# 对social_degree的分析
# 准备数据
X_control1 <- X[, !colnames(X) %in% c("social_degree")]
d1 <- X[, "social_degree"]

# 运行正交估计
set.seed(480)
social_resids <- orthoLTE(x=X_control1, 
                          d=d1, 
                          y=y, 
                          dreg=dreg, 
                          yreg=yreg, 
                          nfold=5)

# 对kinship_degree的分析
# 准备数据
X_control2 <- X[, !colnames(X) %in% c("kinship_degree")]
d2 <- X[, "kinship_degree"]

# 运行正交估计
set.seed(480)
kinship_resids <- orthoLTE(x=X_control2, 
                           d=d2, 
                           y=y, 
                           dreg=dreg, 
                           yreg=yreg, 
                           nfold=5)

# 整理结果
results_ortho <- data.frame(
  Variable = c("Social Degree", "Kinship Degree"),
  Coefficient = c(social_resids$gam, kinship_resids$gam),
  Std_Error = c(social_resids$se, kinship_resids$se)
)

results_ortho <- results_ortho %>%
  mutate(
    CI_lower = Coefficient - 1.96 * Std_Error,
    CI_upper = Coefficient + 1.96 * Std_Error
  )

# # 使用kable展示结果
# kable(results_ortho %>%
#         mutate(
#           Coefficient = sprintf("%.3f", Coefficient),
#           Std_Error = sprintf("%.3f", Std_Error),
#           CI = sprintf("[%.3f, %.3f]", CI_lower, CI_upper)
#         ) %>%
#         select(Variable, Coefficient, Std_Error, CI),
#       caption = "Treatment Effects (Orthogonal Machine Learning)",
#       col.names = c("Network Type", "Coefficient", "Std. Error", "95% CI")) %>%
#   kable_styling(bootstrap_options = c("striped", "hover", "condensed", "responsive"),
#                 full_width = TRUE) %>%
#   column_spec(1, bold = TRUE, width = "15em") %>%
#   column_spec(2:4, width = "12em") %>%
#   row_spec(0, bold = TRUE) %>%
#   footnote(
#     general = "Note: Estimates from Orthogonal Machine Learning with 5-fold cross-validation.",
#     number = c(
#       "Robust standard errors using HC variance estimator.",
#       "Controls include dynasty, region, and status variables."
#     )
#   )

