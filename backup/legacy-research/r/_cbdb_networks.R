#-------------------------------
# 创建关系网络视图
#-------------------------------
#-------------------------------
# 1. 亲属关系网络
#-------------------------------
# 创建亲属关系网络，包含重要的亲属关系信息
kinship_network <- df_KIN_DATA %>%
  # 连接亲属关系代码表获取关系类型
  left_join(df_KINSHIP_CODES, by = c("c_kin_code" = "c_kincode")) %>%
  mutate(c_kin_id = as.character(c_kin_id)) %>%
  # 连接人物信息表获取亲属姓名
  left_join(df_BIOG_MAIN %>% select(c_kin_id = c_personid, c_name),
            by = "c_kin_id") %>%
  # 清理和重命名列
  select(-ends_with(".y")) %>%
  rename_with(~str_remove(., "\\.x$"), ends_with(".x"))

# 创建简化版本的亲属网络，只保留核心变量
kinship_network_simple <- kinship_network %>%
  select(
    person_id = c_personid,          # [主体人物ID] 被研究的历史人物的ID
    relative_id = c_kin_id,          # [亲属ID] 与主体人物有亲属关系的人的ID
    relative_name = c_name,          # [亲属姓名] 亲属的名字
    relation_chn = c_kinrel_chn,     # [中文关系] 亲属关系的中文描述（如：父、母、兄、弟）
    relation_eng = c_kinrel,         # [英文关系] 亲属关系的英文描述
    
    # 亲属关系距离指标
    generation_up = c_upstep,        # [上代距离] 向上数的世代距离（如：父=1，祖父=2）
    generation_down = c_dwnstep,     # [下代距离] 向下数的世代距离（如：子=1，孙=2）
    marriage_step = c_marstep,       # [婚姻距离] 通过婚姻关系产生的距离
    collateral_step = c_colstep      # [旁系距离] 同辈之间的横向距离（如：兄弟姐妹）
  )

# 创建查询亲属关系的函数
get_person_kinship <- function(person_id) {
  kinship_network_simple %>%
    filter(person_id == !!person_id) %>%
    # 按照亲属关系的远近排序
    arrange(
      desc(generation_up),    # 首先按上代关系排序（祖辈在前）
      generation_down,        # 然后是下代关系（子孙）
      marriage_step,          # 接着是婚姻关系
      collateral_step         # 最后是同辈旁系关系
    ) %>%
    # 添加关系类型分类
    mutate(
      relation_type = case_when(
        generation_up > 0 ~ "上代亲属",      # 父母、祖父母等
        generation_down > 0 ~ "下代亲属",    # 子女、孙子女等
        marriage_step > 0 ~ "姻亲关系",      # 配偶及其亲属
        collateral_step > 0 ~ "同辈亲属",    # 兄弟姐妹等
        TRUE ~ "其他关系"
      )
    )
}

# 专门用于获取直系亲属的函数
get_direct_relatives <- function(person_id) {
  kinship_network_simple %>%
    filter(
      person_id == !!person_id,
      # 直系亲属的定义：只有代际距离，没有旁系和婚姻距离
      (generation_up > 0 | generation_down > 0) &  # 有上下代关系
        collateral_step == 0 &                       # 没有旁系距离
        marriage_step == 0                           # 没有婚姻关系
    ) %>%
    arrange(desc(generation_up), generation_down)
}

# 专门用于获取姻亲关系的函数
get_marriage_relatives <- function(person_id) {
  kinship_network_simple %>%
    filter(
      person_id == !!person_id,
      marriage_step > 0    # 只选择有婚姻关系的亲属
    ) %>%
    arrange(marriage_step)
}

# 专门用于获取同辈亲属的函数
get_peer_relatives <- function(person_id) {
  kinship_network_simple %>%
    filter(
      person_id == !!person_id,
      generation_up == 0,      # 没有上代距离
      generation_down == 0,    # 没有下代距离
      collateral_step > 0      # 有旁系距离
    ) %>%
    arrange(collateral_step)
}

#-------------------------------
# 2. 社会关系网络
#-------------------------------

# 整合所有正向社会关系
positive_social_relations <- list(
  
  # 1. 师生/学术关系
  academic = c(
    "為Y之學生",
    "為Y之弟子",
    "從Y遊", 
    "為Y之門人",
    "同學、同門",
    "傳Y之學",
    "論學",
    "讚揚Y之學",
    "研讀Y的著作",
    "向Y問學"
  ),
  
  # 2. 政治关系
  political = c(
    "推薦",
    "為Y之部將",
    "為Y之幕僚",
    "為Y之謀士",
    "同僚",
    "政見趨同",
    "上司為Y",
    "下屬為Y"
  ),
  
  # 3. 门生故吏关系
  patronage = c(
    "是Y的恩主",
    "欣賞/器重",
    "支持",
    "得到Y的喜爱",
    "禮待",
    "為Y所佑(政治關係)"
  ),
  
  # 4. 交游关系
  social = c(
    "友",
    "同年友",
    "同鄉",
    "相識",
    "詩社成員",
    "相唱和",
    "同道"
  ),
  
  # 5. 文献编撰关系
  literary = c(
    "為Y所著書作序",
    "為Y作墓誌銘",
    "為Y作傳",
    "為Y作行狀",
    "編輯Y的學術作品",
    "為Y作神道碑",
    "為Y作墓表",
    "為Y作家傳"
  ),
  
  # 6. 艺术交流关系
  artistic = c(
    "題Y之畫作",
    "贈畫",
    "書、畫為Y所稱道",
    "為Y篆匾額、器銘",
    "畫贊(畫像記)由Y所作"
  ),
  
  # 7. 礼仪往来关系
  ceremonial = c(
    "向Y致賀",
    "贈詩、文",
    "送別",
    "獻文、書于Y",
    "給Y錢物"
  ),
  
  # 8. 通信关系
  correspondence = c(
    "致書Y",
    "答Y書",
    "致Y啓",
    "答Y啓"
  ),
  
  # 9. 服务关系
  service = c(
    "以醫術事Y",
    "醫愈",
    "侍奉",
    "代Y作文"
  ),
  
  # 10. 经济互助关系
  economic = c(
    "貸給Y",
    "借書給Y",
    "給Y錢物"
  )
)

# 创建分析函数
analyze_positive_relations <- function(person_id) {
  # 基础查询
  query <- df_ASSOC_DATA %>%
    left_join(df_ASSOC_CODES, by = "c_assoc_code") %>%
    left_join(df_BIOG_MAIN %>% select(c_personid, name = c_name),
              by = "c_personid")
  
  # 提取所有正向关系
  all_positive_relations <- unlist(positive_social_relations)
  
  # 过滤正向关系并预处理
  base_relations <- query %>%
    filter(c_assoc_desc_chn %in% all_positive_relations,
           c_personid == person_id | c_assoc_id == person_id) %>%
    mutate(
      relation_type_chn = case_when(
        c_assoc_desc_chn %in% positive_social_relations$academic ~ "学术关系",
        c_assoc_desc_chn %in% positive_social_relations$political ~ "政治关系",
        c_assoc_desc_chn %in% positive_social_relations$patronage ~ "门生故吏关系",
        c_assoc_desc_chn %in% positive_social_relations$social ~ "交游关系",
        c_assoc_desc_chn %in% positive_social_relations$literary ~ "文献编撰关系",
        c_assoc_desc_chn %in% positive_social_relations$artistic ~ "艺术交流关系",
        c_assoc_desc_chn %in% positive_social_relations$ceremonial ~ "礼仪往来关系",
        c_assoc_desc_chn %in% positive_social_relations$correspondence ~ "通信关系",
        c_assoc_desc_chn %in% positive_social_relations$service ~ "服务关系",
        c_assoc_desc_chn %in% positive_social_relations$economic ~ "经济互助关系",
        TRUE ~ "其他"
      ),
      relation_type = case_when(
        relation_type_chn == "学术关系" ~ "Academic",
        relation_type_chn == "政治关系" ~ "Political",
        relation_type_chn == "门生故吏关系" ~ "Patronage",
        relation_type_chn == "交游关系" ~ "Social",
        relation_type_chn == "文献编撰关系" ~ "Literary",
        relation_type_chn == "艺术交流关系" ~ "Artistic",
        relation_type_chn == "礼仪往来关系" ~ "Ceremonial",
        relation_type_chn == "通信关系" ~ "Correspondence",
        relation_type_chn == "服务关系" ~ "Service",
        relation_type_chn == "经济互助关系" ~ "Economic",
        TRUE ~ "Other"
      ),
      # 创建标准化的人物对
      person1 = if_else(c_personid == person_id, c_personid, c_assoc_id),
      person2 = if_else(c_personid == person_id, c_assoc_id, c_personid)
    ) %>%
    dplyr::select(c_person_id = person1, c_assoc_id = person2, 
                  relation_type_chn, relation_type) %>%
    unique()
  
  
  return(base_relations)
}


#-------------------------------
# 3. 社会地位
#-------------------------------

# 社会地位分析函数
analyze_social_status <- function(person_id) {
  
  # 1. 官职信息分析
  official_positions <- df_POSTED_TO_OFFICE_DATA %>%
    filter(c_personid == person_id) %>%
    left_join(df_OFFICE_CODES, by = "c_office_id") %>%
    arrange(c_firstyear) %>%
    mutate(
      office_rank = case_when(
        str_detect(c_office_chn, "宰相|丞相|丞相|參知政事|同平章事") ~ 9,
        str_detect(c_office_chn, "尚書|侍郎") ~ 8,
        str_detect(c_office_chn, "給事中|御史中丞") ~ 7,
        str_detect(c_office_chn, "知州|通判") ~ 6,
        str_detect(c_office_chn, "縣令|知縣") ~ 5,
        TRUE ~ NA_real_
      )
    )
  
  # 2. 科举信息分析
  examination_info <- df_ENTRY_DATA %>%
    filter(c_personid == person_id) %>%
    left_join(df_ENTRY_CODES, by = "c_entry_code") %>%
    arrange(c_year) %>%
    mutate(
      exam_rank = case_when(
        str_detect(c_entry_desc_chn, "進士及第") ~ 5,
        str_detect(c_entry_desc_chn, "進士|同進士出身") ~ 4,
        str_detect(c_entry_desc_chn, "舉人|解元") ~ 3,
        # str_detect(c_entry_desc_chn, "生員|秀才") ~ 2,
        TRUE ~ 1
      )
    )
  
  # 3. 社会关系网络分析
  social_network <- df_ASSOC_DATA %>%
    filter(c_personid == person_id | c_assoc_id == person_id) %>%
    left_join(df_ASSOC_CODES, by = "c_assoc_code") %>%
    mutate(
      relation_weight = case_when(
        str_detect(c_assoc_desc_chn, "師|弟子|門人") ~ 5,
        str_detect(c_assoc_desc_chn, "友|同年") ~ 4,
        str_detect(c_assoc_desc_chn, "推薦|薦舉") ~ 4,
        str_detect(c_assoc_desc_chn, "著作|文集") ~ 3,
        TRUE ~ 1
      )
    )
  
  # # 4. 著作与文集分析
  # writings <- df_TEXT_DATA %>%
  #   filter(c_personid == person_id) %>%
  #   left_join(df_TEXT_CODES, by = "c_text_code")
  
  # # 5. 入传情况分析
  biographical_entries <- df_BIOG_SOURCE_DATA %>%
    filter(c_personid == person_id,
           c_self_bio > 0) 
  
  # 6. 文化地位
  culture_status <- df_STATUS_DATA %>%
    left_join(df_STATUS_CODES) %>%
    filter(c_personid == person_id,
           str_detect(c_status_desc_chn, "詩人|史學家|文學家|學者"))
  
  # 7. 社会评价
  social_evaluation <- df_ALTNAME_DATA %>%
    left_join(df_ALTNAME_CODES, by = c("c_alt_name_type_code" = "c_name_type_code")) %>%
    filter(c_personid == person_id,
           str_detect(c_name_type_desc_chn, "謚號|諡號|追贈|先生|夫子|子"))
  
  # 计算综合社会地位指数
  status_index <- list(
    # 官职最高等级
    if_official = max(as.integer(official_positions$office_rank > 0), na.rm = TRUE),
    
    # 科举最高等级
    if_exam = max(as.integer(examination_info$exam_rank > 0), na.rm = TRUE),
    
    # # 社会网络规模和质量
    # network_score = 
    #   sum(social_network$relation_weight),
    
    # # 著作数量
    # writings_count = nrow(writings),
    
    # # 入传数量
    if_biographical = max(as.integer(nrow(biographical_entries) > 0), na.rm = TRUE),

    # 是否有谥号
    if_posthumous = max(as.integer(nrow(culture_status) > 0), na.rm = TRUE),
    
    # 社会评价指标
    if_recognition = max(as.integer(nrow(social_evaluation) > 0), na.rm = TRUE)
      
  )
  
  # 职业生涯轨迹
  career_trajectory <- official_positions %>%
    arrange(c_firstyear) %>%
    select(year = c_firstyear,
           office = c_office_pinyin,
           office_chn = c_office_chn,
           rank = office_rank)
  
  # 社会网络质量
  network_quality <- social_network %>%
    group_by(c_assoc_desc_chn) %>%
    summarise(
      count = n(),
      avg_weight = mean(relation_weight),
      .groups = "drop"
    )
  
  # 返回结果
  return(list(
    basic_status_index = status_index,
    career_path = career_trajectory,
    network_analysis = network_quality,
    examination_data = examination_info,
    # writings_data = writings,
    biographical_data = biographical_entries
  ))
}

# # 添加时期对比分析
# analyze_status_in_context <- function(person_id, year_range = 20) {
#   # 获取个人基本信息
#   person_info <- df_BIOG_MAIN %>%
#     filter(c_personid == person_id)
#   
#   # 获取同时期人物
#   contemporaries <- df_BIOG_MAIN %>%
#     filter(between(c_birthyear, 
#                    person_info$c_birthyear - year_range,
#                    person_info$c_birthyear + year_range))
#   
#   # 分析同时期人物的社会地位
#   contemporary_analysis <- map_df(contemporaries$c_personid,
#                                   analyze_social_status)
#   
#   # 计算相对排名
#   relative_ranking <- list(
#     official_rank = rank(desc(contemporary_analysis$max_official_rank)),
#     exam_rank = rank(desc(contemporary_analysis$max_exam_rank)),
#     network_score = rank(desc(contemporary_analysis$network_score)),
#     writings_count = rank(desc(contemporary_analysis$writings_count))
#   )
#   
#   return(list(
#     person_status = analyze_social_status(person_id),
#     contemporary_stats = summary(contemporary_analysis),
#     relative_position = relative_ranking
#   ))
# }

# 可视化社会地位变化
plot_status_trajectory <- function(person_id) {
  status_data <- analyze_social_status(person_id)
  
  # 绘制官职变化轨迹
  ggplot(status_data$career_path, 
         aes(x = year, y = rank)) +
    geom_line() +
    geom_point() +
    labs(title = "官职生涯轨迹",
         x = "年份",
         y = "官职等级") +
    theme_minimal()
}


#-------------------------------
# 4. 地理空间关系网络
#-------------------------------
geographic_network <- df_BIOG_ADDR_DATA %>%
  # 连接地址代码表
  left_join(df_ADDR_CODES, by = "c_addr_id") %>%
  # 连接地址类型代码表
  left_join(df_BIOG_ADDR_CODES, by = "c_addr_type") %>%
  # 连接人物信息
  left_join(df_BIOG_MAIN %>% select(c_personid, c_name),
            by = "c_personid") %>%
  # 清理和重命名列
  select(-ends_with(".y")) %>%
  rename_with(~str_remove(., "\\.x$"), ends_with(".x")) %>%
  select(
    # 基础信息
    person_id = c_personid,          # [人物ID] 人物唯一标识
    person_name = c_name,            # [人物姓名] 
    
    # 地点信息
    addr_id = c_addr_id,             # [地址ID] 地点唯一标识
    addr_name = c_name_chn,          # [地名] 地点中文名称
    addr_type = c_addr_type,         # [地址类型] 如籍贯、出生地、居住地等
    addr_desc = c_addr_desc_chn,     # [地址描述] 地点详细描述
    
    # 地理坐标
    longitude = x_coord,             # [经度] 地点的经度坐标
    latitude = y_coord,              # [纬度] 地点的纬度坐标
    
    # 时间信息
    first_year = c_firstyear,        # [开始年份] 在该地的起始年份
    last_year = c_lastyear,          # [结束年份] 在该地的结束年份
    
    # 其他重要信息
    sequence = c_sequence,           # [序列号] 地点记录的时间顺序
    is_natal = c_natal              # [是否籍贯] 是否为籍贯地
  )

# 2. 创建一个获取人物生平地理轨迹的函数
get_person_geographic_trajectory <- function(person_id) {
  trajectory <- geographic_network_simple %>%
    # 筛选特定人物
    filter(person_id == !!person_id) %>%
    # 按时间排序
    arrange(first_year, sequence) %>%
    # 添加地点类型说明
    # mutate(
    #   location_type = case_when(
    #     is_natal == "1" ~ "籍贯",
    #     addr_type == "1" ~ "出生地",
    #     addr_type == "2" ~ "居住地",
    #     addr_type == "3" ~ "任职地",
    #     addr_type == "4" ~ "卒地",
    #     TRUE ~ "其他"
    #   ),
      mutate(
        location_type = case_when(
          is_natal == "1" ~ "Native Place",
          addr_type == "1" ~ "Birthplace",
          addr_type == "2" ~ "Residence",
          addr_type == "3" ~ "Office Location",
          addr_type == "4" ~ "Death Place",
          TRUE ~ "Other"
        ),
        # Add period description
        period = case_when(
          is.na(first_year) & is.na(last_year) ~ "Unknown Period",
          is.na(last_year) ~ sprintf("Year %d", first_year),
          TRUE ~ sprintf("%d-%d", first_year, last_year)
        )
      ) %>%
        # Select display columns
        select(
          location = addr_name,
          type = location_type,
          period = period,
          description = addr_desc,
          longitude = longitude,
          latitude = latitude
        )
      return(trajectory)
}



