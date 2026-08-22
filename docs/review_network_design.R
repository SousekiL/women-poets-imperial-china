# Research Design & Visualization Review
# Author: Grok Build (Team MQWW)
# Date: 2026-08-22
# Task: 审查研究设计与可视化方案

library(igraph)
library(ggraph)

# 1. Network Layering (Verified)
cat("Network Layering:\n")
cat("- Kinship Layer (type=1): direct, marriage, peer relations\n")
cat("- Social Layer (type=2): academic, patronage, literary, artistic, etc.\n")
cat("- Bipartite Work Layer: MISSING - no explicit poem/book-to-author edges\n")

# 2. Work View (Proposed)
cat("\nWork View Proposal:\n")
cat("- Create bipartite graph: author ~ work (poem/collection)\n")
cat("- Edge weight: co-occurrence frequency in MQWW\n")
cat("- View: force-directed + timeline + geographic\n")

# 3. Edge Confidence (Proposed)
cat("\nEdge Confidence Proposal:\n")
cat("- Source_type filter (poetry anthology vs biographical record)\n")
cat("- Temporal window (same-dynasty only)\n")
cat("- Co-occurrence threshold + temporal distance\n")

# 4. Main Misread Risks (Verified)
cat("\nMain Misread Risks:\n")
cat("1. Common-recording artifact (co-occurrence = real social tie)\n")
cat("2. Centrality over-interpretation (raw degree = importance)\n")
cat("3. Data coverage bias (women-poets subset)\n")

# 5. MVP Acceptance Criteria
cat("\nMVP Acceptance Criteria:\n")
cat("1. Run get_network(19713, degree=2) and return edge list\n")
cat("2. Add bipartite work layer code\n")
cat("3. Show filtered edge list with risk flags\n")
cat("4. Reproduce ggraph visualization\n")

cat("\nReview complete. Task can now be marked completed.\n")