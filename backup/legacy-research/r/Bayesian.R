# --- 0. 初始设置、加载数据与包 ---
# 确保已加载必要的包
# install.packages(c("rjags", "coda", "dplyr", "ggplot2", "bayesplot", "gt", "here"))
library(rjags)
library(coda)
library(dplyr)
library(ggplot2)
library(bayesplot)
library(gt)
library(here) # 用于更稳健地处理文件路径 (可选)

# 设置工作目录 (如果脚本不在项目根目录，请取消注释并修改)
# setwd(here())
# print(paste("Current working directory:", getwd()))
# 定义图片保存路径
plot_dir <- here("plot_bayes_simplified") # 为这个分析创建一个新的图片子目录
if (!dir.exists(plot_dir)) {
  dir.create(plot_dir, recursive = TRUE)
  print(paste("Created directory for plots:", plot_dir))
}
color_scheme_set("brightblue") # bayesplot颜色方案

# --- 1. 数据准备 ---
# 假设 df_with_metrics 是您包含虚拟变量的数据框
# library(dplyr)
# library(tidyr) # for pivot_longer, if needed, or stringr
# library(stringr) # for str_extract


df_to_process <- df_with_metrics

# 1. 找出所有 dynasty.* 列
dynasty_dummy_cols <- grep("^dynasty\\.", names(df_to_process), value = TRUE)

if (length(dynasty_dummy_cols) == 0) {
  stop("No columns starting with 'dynasty.' found. Please check your column names.")
}

# 2. 将这些虚拟变量转换为长格式，然后提取朝代名称
#   并为每个观测找到其对应的朝代名称
#   (假设每行只有一个 dynasty.* 列为 1)

# 创建一个空的 dynasty_name 列
df_to_process$dynasty_name <- NA 

# 遍历每一行来确定朝代
for (i in 1:nrow(df_to_process)) {
  # 找到当前行为1的 dynasty 虚拟变量列
  active_dynasty_col <- NA
  for (col_name in dynasty_dummy_cols) {
    if (df_to_process[i, col_name] == 1) {
      active_dynasty_col <- col_name
      break # 找到后就跳出内部循环
    }
  }
  
  if (!is.na(active_dynasty_col)) {
    # 从列名中提取朝代名称 (例如，从 "dynasty.Tang" 提取 "Tang")
    # 或者如您所说，如果列名是 dynasty.x1, dynasty.x2, x1, x2 就是朝代名
    # 我们使用 stringr::str_remove 来移除 "dynasty." 前缀
    df_to_process$dynasty_name[i] <- stringr::str_remove(active_dynasty_col, "^dynasty\\.")
  } else {
    # 如果某一行所有的 dynasty.* 虚拟变量都不是1 (理论上不应该发生，除非有缺失或编码错误)
    df_to_process$dynasty_name[i] <- "UnknownOrReference" # 或者设为NA，然后处理
    warning(paste("Row", i, "has no active dynasty dummy variable or multiple are active."))
  }
}

# 3. 将 dynasty_name 转换为因子，并创建 dynasty_id
if (sum(is.na(df_to_process$dynasty_name)) > 0) {
  warning("There are NA values in 'dynasty_name'. These will become a separate factor level or an NA ID.")
  # 您可能需要在这里处理这些NA值，例如将它们归为一个特定的类别或移除这些行
}

df_to_process$dynasty_name_factor <- factor(df_to_process$dynasty_name)
df_to_process$dynasty_id <- as.numeric(df_to_process$dynasty_name_factor)
J_dynasties <- length(levels(df_to_process$dynasty_name_factor))

# 现在 df_to_process 数据框中应该有了 dynasty_name (因子) 和 dynasty_id (数值) 列
# 您可以将 df_to_process (或其训练集部分) 用于后续的贝叶斯模型拟合
# 例如，在准备 data_jags_list 时:
# data_jags_list$dynasty_id <- df_to_process_train_set$dynasty_id # (假设您有训练集)
# data_jags_list$J_dynasties <- J_dynasties


# 确保因变量 is_bieji 是 0/1 整数
df_to_process$is_bieji <- as.integer(as.character(df_to_process$is_bieji))

# 选择固定效应预测变量 (简化版)
df_to_process_by <- df_to_process %>% 
  dplyr::select(is_bieji,
         dynasty_name,
         dynasty_id,
         kinship_degree, social_degree)


# 确保 dynasty_id 是数值型，并获取 J_dynasties
# 如果 dynasty_id 已经是数值型并且是从1到J，则可以直接使用
# 如果 dynasty_name 是因子，dynasty_id 是其数值表示，也很好
if (!is.numeric(df_to_process_by$dynasty_id)) {
  warning("'dynasty_id' is not numeric. Attempting to convert from 'dynasty_name' factor.")
  if (is.factor(df_to_process_by$dynasty_name)) {
    df_to_process_by$dynasty_id <- as.numeric(df_to_process_by$dynasty_name)
  } else {
    df_to_process_by$dynasty_name_factor <- factor(df_to_process_by$dynasty_name)
    df_to_process_by$dynasty_id <- as.numeric(df_to_process_by$dynasty_name_factor)
    print("Created 'dynasty_id' from 'dynasty_name'.")
  }
}
J_dynasties <- length(unique(df_to_process_by$dynasty_id[!is.na(df_to_process_by$dynasty_id)]))

# 获取朝代名称与ID的映射，用于后续绘图标签
if (J_dynasties > 0 && "dynasty_name" %in% names(df_to_process_by)) {
  if(!is.factor(df_to_process_by$dynasty_name)) df_to_process_by$dynasty_name <- factor(df_to_process_by$dynasty_name)
  dynasty_levels_map <- data.frame(
    Name = levels(df_to_process_by$dynasty_name),
    ID = 1:length(levels(df_to_process_by$dynasty_name)) # 假设as.numeric(factor)的顺序
  )
  # 确保映射与实际使用的dynasty_id一致
  # 如果dynasty_id不是从1开始的连续整数，这里的映射需要调整
  # print("Mapping from dynasty name to dynasty_id (based on factor levels):")
  # print(dynasty_levels_map)
} else {
  warning("Cannot create dynasty name map for plot labels.")
  dynasty_levels_map <- data.frame(Name=paste0("DynastyID_",1:J_dynasties), ID=1:J_dynasties) # 后备标签
}


# 标准化连续固定效应预测变量: kinship_degree, social_degree
# 为简单起见，在整个数据集上进行标准化。
# 如果您有严格的训练/测试划分用于贝叶斯模型评估，应在训练集上计算均值/标准差，然后应用到测试集。
df_bayes_model_data <- df_to_process_by
continuous_predictors_bayes <- c("kinship_degree", "social_degree")
means_bayes_std_final <- list()
sds_bayes_std_final <- list()

for (pred_name in continuous_predictors_bayes) {
  if (is.numeric(df_bayes_model_data[[pred_name]]) && length(unique(df_bayes_model_data[[pred_name]])) > 2) { # 仅标准化连续变量
    mean_val <- mean(df_bayes_model_data[[pred_name]], na.rm = TRUE)
    sd_val <- sd(df_bayes_model_data[[pred_name]], na.rm = TRUE)
    if (sd_val > 1e-6 && !is.na(sd_val)) { # 避免除以0或NA，且标准差不应过小
      df_bayes_model_data[[paste0(pred_name, "_std")]] <- (df_bayes_model_data[[pred_name]] - mean_val) / sd_val
      means_bayes_std_final[[pred_name]] <- mean_val
      sds_bayes_std_final[[pred_name]] <- sd_val
      # print(paste("Standardized:", pred_name, "as", paste0(pred_name, "_std")))
    } else {
      # print(paste("Skipped standardization for", pred_name, "as SD is 0, NA or very small. Using original values or setting to 0 if constant."))
      # 如果SD为0，该变量是常数。JAGS可能不喜欢常数作为预测变量。
      # 为避免错误，如果SD为0，可以考虑不包含该变量，或将其值设为0（如果它是中心化的）。
      # 这里我们先创建列，如果SD为0，则其标准化值为0（如果均值也为0）或NA（如果均值非0）。
      # JAGS数据准备时需要处理NA。
      if (sd_val < 1e-6) df_bayes_model_data[[paste0(pred_name, "_std")]] <- 0 # 如果是常数，标准化后为0（如果已中心化）
    }
  } else {
    # print(paste("Predictor", pred_name, "is not numeric or has too few unique values for standardization. Using original values."))
    df_bayes_model_data[[paste0(pred_name, "_std")]] <- df_bayes_model_data[[pred_name]] # 保留原样
  }
}
# 确保所有标准化的列都存在
if (!all(paste0(continuous_predictors_bayes, "_std") %in% names(df_bayes_model_data))) {
  stop("Not all predictors were successfully standardized and added to the dataframe.")
}


# 准备JAGS的数据列表
# 移除包含NA的行 (特别是标准化后可能产生的NA，或dynasty_id中的NA)
df_jags_final_data <- df_bayes_model_data %>%
  filter(!is.na(is_bieji), 
         !is.na(kinship_degree_std), 
         !is.na(social_degree_std), 
         !is.na(dynasty_id))


data_jags_final <- list(
  is_bieji = df_jags_final_data$is_bieji,
  N = nrow(df_jags_final_data),
  J_dynasties = J_dynasties, # 使用之前计算的 J_dynasties
  dynasty_id = df_jags_final_data$dynasty_id,
  kinship_degree = df_jags_final_data$kinship_degree_std, # 使用标准化后的变量
  social_degree = df_jags_final_data$social_degree_std   # 使用标准化后的变量
)
# # 检查数据列表中的NA
# sapply(data_jags_final, function(x) sum(is.na(x)))
# 

# --- 2. 定义 JAGS 模型字符串 ---
jags_model_string_final <- "
model {
  # Likelihood
  for (i in 1:N) {
    is_bieji[i] ~ dbern(p[i])      # 伯努利似然
    logit(p[i]) <- beta0 +           # 截距
                    beta_kinship_degree * kinship_degree[i] +
                    beta_social_degree * social_degree[i] +
                    u_dynasty[dynasty_id[i]]  # 按朝代的随机截距
  }

  # Priors for fixed effects (固定效应的先验)
  beta0 ~ dnorm(0, 0.01)                # 截距 (sd=10, 弱信息)
  beta_kinship_degree ~ dnorm(0, 0.01)  # kinship_degree 系数 (sd=10)
  beta_social_degree ~ dnorm(0, 0.01)   # social_degree 系数 (sd=10)

  # Priors for random effects (dynasty intercepts) (随机效应的先验)
  for (j in 1:J_dynasties) {
    u_dynasty[j] ~ dnorm(0, tau_dynasty) # 每个朝代的随机截距
  }

  # Hyperprior for random effects precision (随机效应精度的超先验)
  tau_dynasty <- pow(sigma_dynasty, -2)
  sigma_dynasty ~ dunif(0, 10)           # 随机效应标准差的弱信息均匀先验
                                         # 备选: sigma_dynasty ~ dnorm(0, 0.1) T(0,) # 半正态 (sd约3)
}
"

# --- 3. 初始值函数 ---
inits_function_final <- function() {
  list(
    beta0 = rnorm(1, 0, 0.1),
    beta_kinship_degree = rnorm(1, 0, 0.1),
    beta_social_degree = rnorm(1, 0, 0.1),
    sigma_dynasty = runif(1, 0.1, 5),
    u_dynasty = rnorm(J_dynasties, 0, 0.1), # 确保 J_dynasties 在函数作用域内可用
    .RNG.name = "base::Wichmann-Hill",
    .RNG.seed = sample(1:1000, 1)
  )
}

# --- 4. 运行 JAGS 模型 ---
# MCMC 设置
n_chains_final <- 3
n_adapt_final <- 5000   # 预热期
n_burnin_final <- 5000  # (可选) 额外老化期
n_iter_final <- 10000   # 采样迭代
n_thin_final <- 10      # 抽样间隔

# 编译模型
# print("Compiling final Bayesian JAGS model...")
jags_model_final_compiled <- NULL
tryCatch({
  jags_model_final_compiled <- jags.model(
    textConnection(jags_model_string_final),
    data = data_jags_final,
    inits = inits_function_final,
    n.chains = n_chains_final,
    n.adapt = n_adapt_final,
    quiet = FALSE
  )
  # print("Final Bayesian JAGS model compiled successfully.")
}, error = function(e_final) {
  # print(paste("Error in final Bayesian jags.model compilation:", e_final$message))
  # print("Please check the JAGS model string, data list (data_jags_final), and initial values.")
  # print("Model string that caused error:")
  # print(jags_model_string_final)
  # print("Data list structure:")
  # print(str(data_jags_final))
  # stop("Stopping due to final Bayesian JAGS compilation error.")
})

# (可选) 额外的老化期
# print("Running additional burn-in phase for final Bayesian model...")
# update(jags_model_final_compiled, n.iter = n_burnin_final, progress.bar = "text")

# 抽样
# print("Running sampling phase for final Bayesian model...")
params_to_monitor_final <- c("beta0", "beta_kinship_degree", "beta_social_degree",
                             "sigma_dynasty", "u_dynasty", "p") # "p" 用于PPC

mcmc_samples_final <- coda.samples(
  jags_model_final_compiled,
  variable.names = params_to_monitor_final,
  n.iter = n_iter_final,
  thin = n_thin_final,
  # progress.bar = "text"
)
# print("Final Bayesian MCMC sampling completed.")

# --- 5. 结果分析与诊断 ---
# print("--- Final Bayesian Model: Convergence Diagnostics ---")
# Gelman-Rubin diagnostic (R-hat)
gelman_results_final <- gelman.diag(mcmc_samples_final, multivariate = FALSE)
# print("Gelman-Rubin diagnostic (R-hat values should be close to 1):")
# print(gelman_results_final$psrf)




