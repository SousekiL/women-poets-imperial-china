get_network <- function(id = 19713, degree = 1) {
  ids_to_process <- id
  all_relations_list <- list()
  
  for(d in 1:degree) {
    current_degree_relations <- lapply(ids_to_process, function(current_id) {
      
      # 使用 tryCatch 处理每种关系查询
      # 直系亲属关系
      direct_relatives <- tryCatch({
        result <- get_direct_relatives(current_id)
        if(nrow(result) > 0) {
          result %>% mutate(relation_type = "direct_kinship")
        } else {
          NULL
        }
      }, error = function(e) NULL)
      
      # 婚姻关系
      marriage_relatives <- tryCatch({
        result <- get_marriage_relatives(current_id)
        if(nrow(result) > 0) {
          result %>% mutate(relation_type = "marriage_kinship")
        } else {
          NULL
        }
      }, error = function(e) NULL)
      
      # 同辈关系
      peer_relatives <- tryCatch({
        result <- get_peer_relatives(current_id)
        if(nrow(result) > 0) {
          result %>% mutate(relation_type = "peer_kinship")
        } else {
          NULL
        }
      }, error = function(e) NULL)
      
      # 合并亲属关系，只处理非空的结果
      kinship_relations <- bind_rows(
        if(!is.null(direct_relatives)) direct_relatives else NULL,
        if(!is.null(marriage_relatives)) marriage_relatives else NULL,
        if(!is.null(peer_relatives)) peer_relatives else NULL
      )
      
      # 如果有亲属关系数据，进行处理
      if(nrow(kinship_relations) > 0) {
        kinship_relations <- kinship_relations %>%
          dplyr::select(
            from = person_id,
            to = relative_id,
            relation_type,
            relation_type_chn = relation_chn
          ) %>%
          mutate(
            from = as.integer(from),
            to = as.integer(to),
            type = 1
          )
      } else {
        kinship_relations <- NULL
      }
      
      # 社会关系
      social_relations <- tryCatch({
        result <- analyze_positive_relations(current_id)
        if(nrow(result) > 0) {
          result %>%
            mutate(
              from = as.integer(c_person_id),
              to = as.integer(c_assoc_id),
              relation_type,
              relation_type_chn
            ) %>%
            select(from, to, relation_type, relation_type_chn) %>%
            mutate(
              from = as.integer(from),
              to = as.integer(to),
              type = 2
            )
        } else {
          NULL
        }
      }, error = function(e) NULL)
      
      # 合并所有关系
      all_relations <- bind_rows(
        if(!is.null(kinship_relations)) kinship_relations else NULL,
        if(!is.null(social_relations)) social_relations else NULL
      )
      
      # 如果没有任何关系，返回NULL
      if(nrow(all_relations) == 0) {
        return(NULL)
      }
      
      # 添加度数信息
      all_relations %>% mutate(degree = d)
    })
    
    # 移除NULL结果并合并当前度的所有关系
    current_degree_relations <- bind_rows(compact(current_degree_relations))
    
    # 如果当前度没有任何关系，跳出循环
    if(nrow(current_degree_relations) == 0) {
      break
    }
    
    all_relations_list[[d]] <- current_degree_relations
    
    # 更新下一轮要处理的ID
    ids_to_process <- unique(c(current_degree_relations$to))
  }
  
  # 合并所有度的关系并去重
  all_relations <- bind_rows(all_relations_list) %>%
    distinct()
  
  # 如果没有找到任何关系，返回空数据框
  if(nrow(all_relations) == 0) {
    return(data.frame(
      from = integer(),
      to = integer(),
      relation_type = character(),
      relation_type_chn = character(),
      type = integer(),
      degree = integer(),
      status = numeric()
    ))
  }
  
  # 获取所有相关人物的ID
  all_person_ids <- unique(c(all_relations$to))
  
  # 计算每个人的社会地位
  person_status <- lapply(all_person_ids, function(x) {
    tryCatch({
      status <- analyze_social_status(x)$basic_status_index
      list(id = x, status = status)
    }, error = function(e) {
      list(id = x, status = NA)
    })
  })
  
  # 转换为数据框
  person_status_df <- do.call(rbind, lapply(person_status, function(x) {
    data.frame(
      to = x$id,
      status = x$status
    )
  }))
  
  # 处理无穷值
  person_status_df <- person_status_df %>%
    mutate(across(
      starts_with("status."),
      ~if_else(is.infinite(.) | is.na(.), 0, .)
    ))
  
  # 合并关系和地位数据
  all_relations <- left_join(all_relations, person_status_df)
  
  return(all_relations)
}


# #-------------------------------
# # 老版本
# #-------------------------------
# 
# 
# get_network <- function(id = 19713, degree = 1) {
#   # # Get Li Qingzhao's person_id
#   # li_qingzhao_id <- df_BIOG_MAIN %>%
#   #   filter(c_name == "Li Qingzhao") %>%
#   #   pull(c_personid)
# 
#   # 存储所有需要查询的ID
#   ids_to_process <- id
#   all_relations_list <- list()
# 
#   # 循环处理每一度的关系
#   for(d in 1:degree) {
#     current_degree_relations <- lapply(ids_to_process, function(current_id) {
# 
#       # Get all types of kinship relations
#       direct_relatives <- get_direct_relatives(current_id) %>%
#         mutate(relation_type = "direct_kinship")
# 
#       marriage_relatives <- get_marriage_relatives(current_id) %>%
#         mutate(relation_type = "marriage_kinship")
# 
#       peer_relatives <- get_peer_relatives(current_id) %>%
#         mutate(relation_type = "peer_kinship")
# 
#       # Combine all kinship relations
#       kinship_relations <- bind_rows(
#         direct_relatives,
#         marriage_relatives,
#         peer_relatives
#       ) %>%
#         dplyr::select(
#           from = person_id,
#           to = relative_id,
#           relation_type,
#           relation_type_chn = relation_chn
#         ) %>%
#         mutate(
#           from = as.integer(from),
#           to = as.integer(to),
#           type = 1
#         )
# 
#       # Get social relations
#       social_relations <- analyze_positive_relations(current_id) %>%
#         mutate(
#           from = as.integer(c_person_id),
#           to = as.integer(c_assoc_id),
#           relation_type,
#           relation_type_chn
#         ) %>%
#         select(from, to, relation_type, relation_type_chn) %>%
#         mutate(
#           from = as.integer(from),
#           to = as.integer(to),
#           type = 2
#         )
# 
#       # Combine all relations
#       # 在合并关系时添加度数信息
#       bind_rows(kinship_relations, social_relations) %>%
#         mutate(degree = d)  # 添加这一行来标记度数
#     })
# 
#     # 合并当前度的所有关系
#     current_degree_relations <- bind_rows(current_degree_relations)
#     all_relations_list[[d]] <- current_degree_relations
# 
#     # 更新下一轮要处理的ID
#     ids_to_process <- unique(c(current_degree_relations$to))
#   }
# 
#   # 合并所有度的关系并去重
#   all_relations <- bind_rows(all_relations_list) %>%
#     distinct()
# 
#   # Get IDs of all related persons
#   all_person_ids <- unique(c(all_relations$to))
# 
#   # Calculate social status for each person
#   person_status <- lapply(all_person_ids, function(x) {
#     status <- analyze_social_status(x)$basic_status_index
#     list(
#       id = x,
#       status = status
#     )
#   })
# 
#   # 转换为数据框
#   person_status_df <- do.call(rbind, lapply(person_status, function(x) {
#     data.frame(
#       to = x$id,
#       status = x$status
#     )
#   }))
# 
#   # 处理无穷值
#   person_status_df <- person_status_df %>%
#     mutate(across(
#       starts_with("status."),
#       ~if_else(is.infinite(.) & . < 0, 0, .)
#     ))
# 
#   # 合并关系和地位数据
#   all_relations <- left_join(all_relations, person_status_df)
# 
#   return(all_relations)
# }

