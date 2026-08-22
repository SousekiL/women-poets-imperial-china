# 检查数据结构和内容
print("vertices_complete 结构:")
str(vertices_complete)
print("
data_real_clean 结构:")
str(data_real_clean)

# 检查节点ID的数值范围
print("
节点ID范围:")
range(vertices_complete$name)
print("
边的节点ID范围:")
range(c(data_real_clean$from, data_real_clean$to))

# 尝试另一种方式创建网络
# 首先确保节点ID是连续的整数
vertices_complete_new <- vertices_complete %>%
  mutate(id = row_number()) %>%
  select(id, everything())

# 创建ID映射
id_mapping <- vertices_complete_new %>%
  select(id, old_id = name)

# 更新边数据中的ID
data_real_clean_new <- data_real_clean %>%
  left_join(id_mapping, by = c("from" = "old_id")) %>%
  rename(new_from = id) %>%
  left_join(id_mapping, by = c("to" = "old_id")) %>%
  rename(new_to = id) %>%
  select(from = new_from, to = new_to, everything(), -c(new_from, new_to))

# 尝试创建网络
network <- tbl_graph(
  nodes = vertices_complete_new %>% select(-name),  # 移除原始name列
  edges = data_real_clean_new,
  directed = FALSE
)
