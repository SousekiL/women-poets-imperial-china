
#-------------------------------
# Plot
#-------------------------------
# 
# plot_text_title_size = 25
# plot_text_normal_size = 20
# plot_text_small_size = 16

plot_text_title_size = 25
plot_text_normal_size = 17
plot_text_small_size = 15


# 获取中心点信息
center_person_info <- df_BIOG_MAIN %>%
  filter(c_personid == center_id) %>%
  select(c_name, c_name_chn) %>%
  collect()

# 计算每个人的status总和
node_status <- data_real %>%
  as.data.frame() %>%
  # 计算status总和
  mutate(status_sum = rowSums(select(., starts_with("status.")))) %>%
  group_by(from, to) %>%
  slice_min(type, n = 1) %>%
  ungroup() %>%
  dplyr::select(from, to, type, status_sum, degree) 

# 获取性别信息
person_gender <- df_BIOG_MAIN %>%
  select(c_personid, c_female) %>%
  mutate(gender = ifelse(c_female == 1, "Female", "Male"),
         c_personid = as.integer(c_personid))

# 修改节点数据创建
vertices <- node_status %>%
  select(from, to, type, status_sum, degree) %>%
  gather(key, node_id, c(from, to)) %>%
  distinct(node_id, .keep_all = TRUE) %>%
  # 添加性别信息
  left_join(person_gender, by = c("node_id" = "c_personid")) %>%
  mutate(
    is_center = node_id == center_id,
    node_type = case_when(
      is_center ~ "Center",
      TRUE ~ gender
    )
  ) %>%
  select(name = node_id, type, status_sum, is_center, gender, node_type)

# 创建网络图
network <- graph_from_data_frame(
  d = select(data_real, from, to, type, degree),
  vertices = vertices
)


# 修改颜色方案
edge_colors <- c(
  "1" = "lightblue",
  "2" = "orange"
)
node_colors <- c(
  "Center" = "#e41a1c",    # 红色为中心节点
  "Female" = "#ff69b4",    # 粉色为女性
  "Male" = "#4169e1"       # 蓝色为男性
)

#-------------------------------
# Curve + nolabel
#-------------------------------

# 创建标题
title_text <- sprintf("Personal Relationship Network of %s (%s)", 
                      center_person_info$c_name, 
                      center_person_info$c_name_chn)

# 可视化代码
p <- ggraph(network, layout = "fr") +
  geom_edge_arc(aes(color = as.factor(type), 
                    linetype = as.factor(degree), 
                    edge_alpha = 0.6),
                width = 0.5,
                strength = 0.2,
                alpha = 0.6) +
  # geom_edge_link(aes(color = as.factor(type)), 
  #                width = 1, 
  #                alpha = 0.6) +
  geom_node_point(aes(size = status_sum,
                      color = node_type,
                      shape = node_type), 
                  alpha = 0.8,
                  stroke = 0.5,
                  color = "black") +
  geom_node_point(aes(size = status_sum,
                      fill = node_type,
                      shape = node_type), 
                  alpha = 0.8,
                  stroke = 0) +
  # geom_node_text(aes(label = name), 
  #                repel = TRUE, 
  #                size = 3) +
  scale_edge_color_manual(values = edge_colors,
                          name = "Edge Type",
                          labels = c("1" = "Kinship Relations", 
                                     "2" = "Social Relations")) +
  scale_edge_linetype_manual(values = c(
    "1" = "solid",      # 一度关系用实线
    "2" = "dashed"      # 二度关系用虚线
  ),
  name = "Degree") +    # 添加线型图例
  scale_fill_manual(values = node_colors,
                    name = "Gender") +
  scale_shape_manual(values = c(
    "Center" = 21,
    "Female" = 21,
    "Male" = 21
  ),
  name = "Gender") +
  # scale_shape_manual(values = c(
  #   "Center" = 18,    # 菱形
  #   "Female" = 16,    # 圆形
  #   "Male" = 16       
  # ),
  # name = "Gender") +
  scale_size_continuous(name = "Social Status Index",
                        range = c(2, 5),
                        guide = guide_legend(keywidth = 0.5, keyheight = 0.5)) +
  theme_graph() +
  labs(title = title_text,
       subtitle = "Node size indicates social status index, colors represent gender") +
  # theme_common()
  theme(
    plot.title = element_text(size = plot_text_title_size, face = "bold", hjust = 0),
    plot.subtitle = element_text(size = plot_text_normal_size, hjust = 0),
    legend.title = element_text(size = plot_text_normal_size),
    legend.text = element_text(size = plot_text_small_size),
    text = element_text(family = "Canger")
  )

# # 或保存为高质量的 JPEG
# ggsave(paste0("plot/", center_person_info$c_name, ".png"),
#        width = 12,
#        height = 8,
#        dpi = 150)     

