## 社会关系
library(magrittr)
library(ggraph)
library(igraph)
library(tidyverse)
theme_set(theme_void())
library(showtext)
## Add the font with the corresponding font faces
font_add("Canger", "/Library/Fonts/仓耳今楷01-W04.ttf")
font_families()

showtext_auto()  # 全局自动使用

library(DBI)
library(RSQLite)
filename <- '/Users/sousekilyu/Documents/Meta Data/CBDB/cbdb202409.db'
sqlite.driver <- dbDriver("SQLite")
db <- dbConnect(sqlite.driver,
                dbname = filename)
df_KIN_DATA <- dbReadTable(db,"KIN_DATA")
df_KINSHIP_CODES <- dbReadTable(db,"KINSHIP_CODES")
df_KIN_MOURNING <- dbReadTable(db,"KIN_MOURNING")
df_KIN_MOURNING_STEPS <- dbReadTable(db,"KIN_MOURNING_STEPS")
df_KIN_DATA$c_personid %<>% as.character()
df_KIN_DATA$c_kin_id %<>% as.character()

kin_name <- df_BIOG_people_s %>%
  select(c_personid, c_name_chn, c_birthyear) %>%
  unique() %>%
  rename(c_kin_id = c_personid, c_kin_name = c_name_chn, c_kin_birthyear = c_birthyear) 
df_kin <- df_BIOG_people_s %>%
  left_join(df_KIN_DATA[, c("c_personid", "c_kin_id", "c_kin_code")]) %>%
  left_join(kin_name) %>%
  left_join(df_KINSHIP_CODES[, c("c_kincode", "c_kinrel_chn", "c_upstep", "c_dwnstep", "c_marstep", "c_colstep")],
            by = c("c_kin_code" = "c_kincode"))

df_kin_s <- select(df_kin, c_female, c_personid, c_dynasty_chn, c_birthyear, c_name_chn, 
                   c_kin_id, c_kin_name, c_kin_code, c_kinrel_chn, c_kin_birthyear,
                   c_upstep, c_dwnstep, c_marstep, c_colstep)
df_kin_s$c_personid %<>% as.character()
df_kin_s$c_kin_id %<>% as.character()
## 篩選沒有父親往上關係的人
df_kin_upbest <- df_kin_s %>%
  group_by(c_personid) %>%
  summarise(c_upstep_sum = sum(c_upstep)) %>%
  ungroup() %>%
  filter(c_upstep_sum == 0) %>%
  left_join(df_kin_s)

### 固定为函数
####### 获取亲属关系
getkin2DF <- function(var) {
  
  var <- as.character(var)
  
  .df_kin_tmp <- df_kin_s %>%
    filter(c_personid == var)
  
  .dt_sth <- data.frame()
  .df_tmp <- .df_kin_tmp
  for(i in 1:1) {
    .df_tmp %<>%
      filter(c_dwnstep >= 1 & c_dwnstep <= 99 & (c_upstep+c_marstep+c_colstep)==0) %>%
      select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
    
    for(j in 1:50) {
      .tmp1 <- .df_tmp
      .dt_sth <- rbind(.dt_sth, .tmp1)
      .df_tmp %<>%
        select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
        rename(c_personid = c_kin_id,
               c_name_chn = c_kin_name,
               c_birthyear = c_kin_birthyear) %>%
        left_join(df_kin_s) %>%
        filter(c_dwnstep >= 1 & c_dwnstep <= 99 & (c_upstep+c_marstep+c_colstep)==0) %>%
        select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
      
      if( length(.df_tmp$c_kin_name) == 0) {
        break
      }
    }
  }
  
  .insert <- data.frame(
    c_personid = NA, 
    c_name_chn = NA, 
    c_birthyear = NA, 
    c_kin_id = NA, 
    c_kin_name = NA, 
    c_kin_birthyear = NA
  )
  .dt_sth %<>% unique()
  .dt_sth_mar <- .dt_sth %>%
    select(c_personid, c_name_chn, c_birthyear) %>%
    left_join(df_kin_s) %>%
    filter(c_marstep == 1 & (c_upstep+c_dwnstep+c_colstep)==0) %>%
    select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
    unique()

  .dt_sth_mar_dwn <- .dt_sth_mar %>%
    select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
    rename(c_personid = c_kin_id, 
           c_name_chn = c_kin_name, 
           c_birthyear = c_kin_birthyear) %>%
    left_join(df_kin_s) %>%
    filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
    select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
    unique()
  if( dim(.dt_sth_mar)[1]==0 ) {
    .dt_sth_mar  <- .insert
  }
  if( dim(.dt_sth_mar_dwn)[1]==0 ) {
    .dt_sth_mar_dwn  <- .insert
  }
  .dt_sth_all <- unique(
    rbind(
      data.frame(
        .dt_sth,
        type = 'dwnstep'
      ),
      data.frame(
        .dt_sth_mar,
        type = 'marstep'
      ),
      data.frame(
        .dt_sth_mar_dwn,
        type = 'dwnstep'
      )
    )
  )
  .dt_sth_all <- .dt_sth_all[!is.na(.dt_sth_all$c_name_chn),]
  return(.dt_sth_all)
}
###### 转化为网络数据

getdt2GRAPH <- function(dt) {
  .edges <- dt %>%
    select(c_personid, c_kin_id, type) %>%
    rename(from = c_personid,
           c_personid = c_kin_id) %>%
    left_join(df_BIOG_people_s) %>%
    select(from, c_personid, c_female, c_birthyear, type) %>%
    arrange(from, c_birthyear) %>%
    rename(to = c_personid)
  .name <- unique(c(as.character(.edges$from), as.character(.edges$to)))
  .vertices <- data.frame(
    c_personid = .name
  ) %>%
    left_join(df_BIOG_people_s) %>%
    select(c_personid, c_name_chn, c_birthyear, c_female) %>%
    rename(name = c_personid)
  
  .flareGraph <- graph_from_data_frame(.edges, vertices = .vertices)
  
  return(.flareGraph)
}






## 以趙匡胤一支為例子
df_kin_tmp <- df_kin_upbest %>%
  filter(c_name_chn == '趙朓')
df_zhao <- data.frame()
df_tmp <- df_kin_tmp
for(i in 1:1) {
  df_tmp %<>%
    filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
    select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
  
  for(j in 1:30) {
    .tmp1 <- df_tmp
    df_zhao <- rbind(df_zhao, .tmp1)
    df_tmp %<>%
      select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
      rename(c_personid = c_kin_id,
             c_name_chn = c_kin_name,
             c_birthyear = c_kin_birthyear) %>%
      left_join(df_kin_s) %>%
      filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
      select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
    
    print(paste0(j, df_tmp$c_kin_name))
  }
}

df_zhao %<>% unique()
df_zhao_mar <- df_zhao %>%
  select(c_personid, c_name_chn, c_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_marstep == 1 & (c_upstep+c_dwnstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()
# 婚姻关系的子女关系
df_zhao_mar_dwn <- df_zhao_mar %>%
  select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
  rename(c_personid = c_kin_id, 
         c_name_chn = c_kin_name, 
         c_birthyear = c_kin_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()

df_zhao_all <- unique(
  rbind(
    data.frame(
      df_zhao,
      type = 'dwnstep'
    ),
    data.frame(
      df_zhao_mar,
      type = 'marstep'
    ),
    data.frame(
      df_zhao_mar_dwn,
      type = 'dwnstep'
    )
  )
)

save(df_zhao_all, file = '/Users/sousekilyu/Library/Mobile Documents/com~apple~CloudDocs/R/Women/data/df_zhao_all.rda')

#####
## 以唐朝一支為例子
df_kin_tmp <- df_kin_s %>%
  filter(c_personid == '31121')


df_li <- data.frame()
df_tmp <- df_kin_tmp
for(i in 1:1) {
  df_tmp %<>%
    filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
    select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
  
  for(j in 1:50) {
    .tmp1 <- df_tmp
    df_li <- rbind(df_li, .tmp1)
    df_tmp %<>%
      select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
      rename(c_personid = c_kin_id,
             c_name_chn = c_kin_name,
             c_birthyear = c_kin_birthyear) %>%
      left_join(df_kin_s) %>%
      filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
      select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
    
    print(paste0(j, df_tmp$c_kin_name))
    
    if( length(df_tmp$c_kin_name) == 0) {
      break
    }
    
  }
}

df_li %<>% unique()
df_li_mar <- df_li %>%
  select(c_personid, c_name_chn, c_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_marstep == 1 & (c_upstep+c_dwnstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()
# 婚姻关系的子女关系
df_li_mar_dwn <- df_li_mar %>%
  select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
  rename(c_personid = c_kin_id, 
         c_name_chn = c_kin_name, 
         c_birthyear = c_kin_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()

df_li_all <- unique(
  rbind(
    data.frame(
      df_li,
      type = 'dwnstep'
    ),
    data.frame(
      df_li_mar,
      type = 'marstep'
    ),
    data.frame(
      df_li_mar_dwn,
      type = 'dwnstep'
    )
  )
)
save(df_li_all, file = '/Users/sousekilyu/Library/Mobile Documents/com~apple~CloudDocs/R/Women/data/df_li_all.rda')


###
## 兰陵萧氏
df_kin_tmp <- df_kin_s %>%
  filter(c_personid == '12250')


dt_xiao <- data.frame()
df_tmp <- df_kin_tmp
for(i in 1:1) {
  df_tmp %<>%
    filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
    select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
  
  for(j in 1:50) {
    .tmp1 <- df_tmp
    dt_xiao <- rbind(dt_xiao, .tmp1)
    df_tmp %<>%
      select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
      rename(c_personid = c_kin_id,
             c_name_chn = c_kin_name,
             c_birthyear = c_kin_birthyear) %>%
      left_join(df_kin_s) %>%
      filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
      select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
    
    print(paste0(j, df_tmp$c_kin_name))
    if( length(df_tmp$c_kin_name) == 0) {
      break
    }
  }
}

dt_xiao %<>% unique()
dt_xiao_mar <- dt_xiao %>%
  select(c_personid, c_name_chn, c_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_marstep == 1 & (c_upstep+c_dwnstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()
# 婚姻关系的子女关系
dt_xiao_mar_dwn <- dt_xiao_mar %>%
  select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
  rename(c_personid = c_kin_id, 
         c_name_chn = c_kin_name, 
         c_birthyear = c_kin_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()

dt_xiao_all <- unique(
  rbind(
    data.frame(
      dt_xiao,
      type = 'dwnstep'
    ),
    data.frame(
      dt_xiao_mar,
      type = 'marstep'
    ),
    data.frame(
      dt_xiao_mar_dwn,
      type = 'dwnstep'
    )
  )
)
save(dt_xiao_all, file = '/Users/sousekilyu/Library/Mobile Documents/com~apple~CloudDocs/R/Women/data/dt_xiao_all.rda')


### 王勃

df_kin_s[which(df_kin_s$c_personid == '30873' &
                 df_kin_s$c_kin_id == '30874'),]$c_upstep <- 0
df_kin_s[which(df_kin_s$c_personid == '30873' &
                 df_kin_s$c_kin_id == '30874'),]$c_dwnstep <- 6

df_kin_tmp <- df_kin_s %>%
  filter(c_personid == '12116')


dt_wang <- data.frame()
df_tmp <- df_kin_tmp
for(i in 1:1) {
  df_tmp %<>%
    filter(c_dwnstep >= 1 & c_dwnstep < 99 & (c_upstep+c_marstep+c_colstep)==0) %>%
    select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
  
  for(j in 1:50) {
    .tmp1 <- df_tmp
    dt_wang <- rbind(dt_wang, .tmp1)
    df_tmp %<>%
      select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
      rename(c_personid = c_kin_id,
             c_name_chn = c_kin_name,
             c_birthyear = c_kin_birthyear) %>%
      left_join(df_kin_s) %>%
      filter(c_dwnstep >= 1 & c_dwnstep < 99 & (c_upstep+c_marstep+c_colstep)==0) %>%
      select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
    
    print(paste0(j, df_tmp$c_kin_name))
    
    if( length(df_tmp$c_kin_name) == 0) {
      break
    }
  }
}

dt_wang %<>% unique()
dt_wang_mar <- dt_wang %>%
  select(c_personid, c_name_chn, c_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_marstep == 1 & (c_upstep+c_dwnstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()
# 婚姻关系的子女关系
dt_wang_mar_dwn <- dt_wang_mar %>%
  select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
  rename(c_personid = c_kin_id, 
         c_name_chn = c_kin_name, 
         c_birthyear = c_kin_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()

dt_wang_all <- unique(
  rbind(
    data.frame(
      dt_wang,
      type = 'dwnstep'
    )
  )
)
save(dt_wang_all, file = '/Users/sousekilyu/Library/Mobile Documents/com~apple~CloudDocs/R/Women/data/dt_wang_all.rda')






## 朱元璋
df_kin_tmp <- df_kin_upbest %>%
  filter(c_name_chn == '朱元璋')
df_zhu <- data.frame()
df_tmp <- df_kin_tmp
for(i in 1:1) {
  df_tmp %<>%
    filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
    select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
  
  for(j in 1:30) {
    .tmp1 <- df_tmp
    df_zhao <- rbind(df_zhu, .tmp1)
    df_tmp %<>%
      select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
      rename(c_personid = c_kin_id,
             c_name_chn = c_kin_name,
             c_birthyear = c_kin_birthyear) %>%
      left_join(df_kin_s) %>%
      filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
      select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear)
    
    print(paste0(j, df_tmp$c_kin_name))
  }
}

df_zhu %<>% unique()
ddf_zhu_mar <- df_zhu %>%
  select(c_personid, c_name_chn, c_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_marstep == 1 & (c_upstep+c_dwnstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()
# 婚姻关系的子女关系
df_zhao_mar_dwn <- df_zhao_mar %>%
  select(c_kin_id, c_kin_name, c_kin_birthyear) %>%
  rename(c_personid = c_kin_id, 
         c_name_chn = c_kin_name, 
         c_birthyear = c_kin_birthyear) %>%
  left_join(df_kin_s) %>%
  filter(c_dwnstep == 1 & (c_upstep+c_marstep+c_colstep)==0) %>%
  select(c_personid, c_name_chn, c_birthyear, c_kin_id, c_kin_name, c_kin_birthyear) %>%
  unique()

df_zhao_all <- unique(
  rbind(
    data.frame(
      df_zhao,
      type = 'dwnstep'
    ),
    data.frame(
      df_zhao_mar,
      type = 'marstep'
    ),
    data.frame(
      df_zhao_mar_dwn,
      type = 'dwnstep'
    )
  )
)

save(df_zhao_all, file = '/Users/sousekilyu/Library/Mobile Documents/com~apple~CloudDocs/R/Women/data/df_zhao_all.rda')

