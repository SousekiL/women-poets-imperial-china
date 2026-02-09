library(dplyr)
library(tidyr)

get_jinshi_geography <- function(index_start, index_end) {
  # # 1. 获取诗人的出生年
  # poet_birth_years <- df_BIOG_MAIN %>%
  #   filter(c_personid %in% df_poets$c_personid) %>%
  #   select(c_personid, c_name, c_birthyear) %>%
  #   filter(!is.na(c_birthyear))
  
  # 2. 对每个诗人，获取其生年前后50年出生的进士
  jinshi_data <- df_ENTRY_DATA %>%
    left_join(df_ENTRY_CODES, by = "c_entry_code") %>%
    filter(str_detect(c_entry_desc_chn, "進士|舉人|解元")) %>%  # 进士编码
    # 连接BIOG_MAIN获取进士的出生年
    left_join(df_BIOG_MAIN %>% 
                select(c_personid, c_birthyear),
              by = "c_personid") %>%
    filter(
      c_birthyear >= index_start, # 开始时间
      c_birthyear <= index_end # 结束时间
      ) %>%
    select(
      jinshi_list = c_personid,
      c_entry_desc_chn
    )
    # 
    # poet_birth_years %>%
    # rowwise() %>%
    # mutate(
    #   period_start = c_birthyear - 50,
    #   period_end = c_birthyear + 50
    # ) %>%
    # # 获取在这个时期出生的进士
    # group_by(c_personid, c_name, c_birthyear, period_start, period_end) %>%
    # summarise(
    #   jinshi_list = list(
    #     df_ENTRY_DATA %>%
    #       left_join(df_ENTRY_CODES, by = "c_entry_code") %>%
    #       filter(str_detect(c_entry_desc_chn, "進士|舉人|解元")) %>%  # 进士编码
    #       # 连接BIOG_MAIN获取进士的出生年
    #       left_join(df_BIOG_MAIN %>% 
    #                   select(c_personid, c_birthyear),
    #                 by = "c_personid") %>%
    #       filter(
    #         c_birthyear >= period_start,
    #         c_birthyear <= period_end
    #       ) %>%
    #       pull(c_personid)
    #   )
    # ) %>%
    # ungroup()
  
  # 3. 获取进士的出生地信息
  jinshi_locations <- jinshi_data %>%
    # 获取进士的出生年和出生地
    left_join(
      df_BIOG_MAIN %>%
        select(c_personid, c_birthyear.jinshi = c_birthyear),
      by = c("jinshi_list" = "c_personid")
    ) %>%
    left_join(
      df_BIOG_ADDR_DATA %>%
        filter(c_addr_type %in% c(1, 5, 7, 8)) %>%  # 籍贯/出生地
        group_by(c_personid) %>%
        slice(which.min(c_addr_type)) %>%  # 只保留每个人最小的c_addr_type对应的行
        ungroup() %>%
        select(c_personid, c_addr_id.jinshi = c_addr_id),
      by = c("jinshi_list" = "c_personid")
    ) %>%
    # 获取地名
    left_join(
      df_ADDR_CODES %>%
        select(c_addr_id.jinshi = c_addr_id, c_name_chn.jinshi = c_name_chn),
      by = "c_addr_id.jinshi"
    ) %>%
    # 获取经纬度
    left_join(
      df_ADDR_XY %>%
        select(c_addr_id.jinshi = c_addr_id, x_coord, y_coord),
      by = "c_addr_id.jinshi"
    )
    # # 获取上级行政区
    # left_join(
    #   df_ADDR_BELONGS_DATA %>%
    #     select(c_addr_id.jinshi = c_addr_id, c_belongs_to),
    #   by = "c_addr_id.jinshi"
    # ) %>%
    # left_join(
    #   df_ADDR_CODES %>%
    #     select(c_addr_id = c_belongs_to, superior_name = c_name_chn),
    #   by = "c_addr_id"
    # )
  
  # # 4. 整理结果
  # results <- jinshi_locations %>%
  #   group_by(c_personid, c_name, c_birthyear) %>%
  #   summarise(
  #     total_jinshi = n_distinct(jinshi_list),
  #     locations = list(tibble(
  #       addr_name = c_name_chn,
  #       superior_name = superior_name,
  #       longitude = x_coord,
  #       latitude = y_coord,
  #       jinshi_count = n(),
  #       avg_jinshi_birthyear = mean(c_birthyear.jinshi, na.rm = TRUE)
  #     ))
  #   ) %>%
  #   ungroup()
  
  return(jinshi_locations)
}
