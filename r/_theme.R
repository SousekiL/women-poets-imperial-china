theme_common <- function() {
  theme_minimal() +
    theme(
      text = element_text(family = "Canger", size = 13),
      # 标题设置
      plot.title = element_text(hjust = 0, size = 25, face = "bold",
                                margin = unit(c(0, 0, 15, 0), "pt")),
      plot.subtitle = element_text(hjust = 0, size = 17,
                                   margin = unit(c(0, 0, 15, 0), "pt")),
      
      # 坐标轴标题
      axis.title = element_text(size = 17),
      
      # 坐标轴刻度文字
      axis.text = element_text(size = 15),
      axis.text.x = element_text(
        #hjust = 1, 
                                 size = 15), # angle = 45, 
      axis.text.y = element_text(size = 15),
      
      # 分面标题
      strip.text = element_text(face = "bold", size = 15),
      
      # 图例设置
      legend.title = element_text(size = 15),
      legend.text = element_text(size = 15),
      legend.position = "bottom",
      
      # 标签文字
      plot.caption = element_text(size = 13, hjust = 1),
      
      # 面板网格线
      panel.grid.major = element_line(color = "gray90"),
      panel.grid.minor = element_line(color = "gray95")
    )
}
