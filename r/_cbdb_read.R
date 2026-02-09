#===============================
# Read data
#===============================

#-------------------------------
# 核心人物信息表
#-------------------------------
# 基础传记信息
df_BIOG_MAIN <- dbReadTable(db, "BIOG_MAIN")  # 人物基本信息
df_BIOG_SOURCE_DATA <- dbReadTable(db, "BIOG_SOURCE_DATA")  # 资料来源数据表
df_ALTNAME_DATA <- dbReadTable(db, "ALTNAME_DATA")  # 别名数据表
df_ALTNAME_CODES <- dbReadTable(db, "ALTNAME_CODES")  # 别名种类代码表
df_TEXT_CODES <- dbReadTable(db, "TEXT_CODES")  
# df_TEXT_DATA <- dbReadTable(db, "TEXT_DATA")  
df_BIOG_SOURCE_DATA <- dbReadTable(db, "BIOG_SOURCE_DATA")  
df_DYNASTIES <- dbReadTable(db, "DYNASTIES")  


#-------------------------------
# 地理信息表
#-------------------------------
df_BIOG_ADDR_DATA <- dbReadTable(db, "BIOG_ADDR_DATA")  # 人物地址关系数据表
df_BIOG_ADDR_CODES <- dbReadTable(db, "BIOG_ADDR_CODES")  # 地址关系类别代码表
df_ADDR_CODES <- dbReadTable(db, "ADDR_CODES")  # 行政单位代码表
df_ADDR_BELONGS_DATA <- dbReadTable(db, "ADDR_BELONGS_DATA")  # 行政单位从属关系
df_ADDR_PLACE_DATA <- dbReadTable(db, "ADDR_PLACE_DATA")  # 经纬度地址数据表
df_ADDR_XY <- dbReadTable(db, "ADDR_XY")  # 经纬度地址数据表

#-------------------------------
# 社会关系表
#-------------------------------
df_ASSOC_DATA <- dbReadTable(db, "ASSOC_DATA")  # 社会关系数据表
df_ASSOC_CODES <- dbReadTable(db, "ASSOC_CODES")  # 社会关系代码表
df_ASSOC_TYPES <- dbReadTable(db, "ASSOC_TYPES")  # 社会关系分类表
df_ASSOC_CODE_TYPE_REL <- dbReadTable(db, "ASSOC_CODE_TYPE_REL")  # 关系代码与类型关系表
df_STATUS_DATA <- dbReadTable(db, "STATUS_DATA")  # 
df_STATUS_CODES <- dbReadTable(db, "STATUS_CODES")  # 師生關係
df_ALTNAME_DATA <- dbReadTable(db, "ALTNAME_DATA")  # 
df_ALTNAME_CODES <- dbReadTable(db, "ALTNAME_CODES")  # 師生關係

#-------------------------------
# 亲属关系表
#-------------------------------
# 亲属关系基础数据
df_KIN_DATA <- dbReadTable(db, "KIN_DATA")  # 亲属关系数据表

# 亲属关系代码表
df_KINSHIP_CODES <- dbReadTable(db, "KINSHIP_CODES")  # 亲属类别代码表

# # 著作关系
# df_TEXT_DATA <- dbReadTable(db, "TEXT_DATA") 

# 丧服制度相关表（可用于分析亲属关系远近）
df_KIN_MOURNING <- dbReadTable(db, "KIN_MOURNING")  # 五服等级中的亲属和服丧种类代码表
df_KIN_MOURNING_STEPS <- dbReadTable(db, "KIN_MOURNING_STEPS")  # 五服亲属与本人的关系代码表

#-------------------------------
# 官职与入仕表
#-------------------------------
df_POSTING_DATA <- dbReadTable(db, "POSTING_DATA")  # 除授数据表
df_POSTED_TO_OFFICE_DATA <- dbReadTable(db, "POSTED_TO_OFFICE_DATA")  # 任职详细数据
df_POSTED_TO_ADDR_DATA <- dbReadTable(db, "POSTED_TO_ADDR_DATA")  # 任职地数据
df_OFFICE_CODES <- dbReadTable(db, "OFFICE_CODES")  # 官僚机构代码表
df_OFFICE_TYPE_TREE <- dbReadTable(db, "OFFICE_TYPE_TREE")  # 官僚机构等级结构

#-------------------------------
# 入仕相关表
#-------------------------------
df_ENTRY_DATA <- dbReadTable(db, "ENTRY_DATA")  # 入仕数据表
df_ENTRY_CODES <- dbReadTable(db, "ENTRY_CODES")  # 入仕方式代码表
df_ENTRY_TYPES <- dbReadTable(db, "ENTRY_TYPES")  # 入仕方式分类表

#-------------------------------
# 统一ID格式
#-------------------------------
id_columns <- c("c_personid", "c_kin_id", "c_assoc_id")
for(df_name in ls(pattern = "^df_")) {
  df <- get(df_name)
  for(col in id_columns) {
    if(col %in% names(df)) {
      df[[col]] <- as.character(df[[col]])
      assign(df_name, df)
    }
  }
}

#-------------------------------
# 创建基础信息视图
#-------------------------------
# 人物基本信息视图
basic_info <- df_BIOG_MAIN %>%
  select(c_personid, c_name) %>%
  left_join(
    df_BIOG_ADDR_DATA %>% 
      filter(c_addr_type == 1) %>%  # 假设1代表籍贯
      select(c_personid, c_addr_id),
    by = "c_personid"
  ) %>%
  left_join(
    df_ADDR_CODES %>% 
      select(c_addr_id, c_name_chn),
    by = "c_addr_id"
  )



df.huwenkai <- fread('/Users/sousekilyu/Documents/Meta Data/CBDB/mqww/cycle/huwenkai.csv')
df.work <- fread('/Users/sousekilyu/Documents/Meta Data/CBDB/mqww/cycle/work.csv')
df.poet <- fread('/Users/sousekilyu/Documents/Meta Data/CBDB/mqww/cycle/poet.csv')
df.work <- fread('/Users/sousekilyu/Documents/Meta Data/CBDB/mqww/cycle/work.csv')
df.poem.poet <- fread('/Users/sousekilyu/Documents/Meta Data/CBDB/mqww/cycle/poempoetlinks.csv')
df.poem.work <- fread('/Users/sousekilyu/Documents/Meta Data/CBDB/mqww/cycle/workpoemlinks.csv')
