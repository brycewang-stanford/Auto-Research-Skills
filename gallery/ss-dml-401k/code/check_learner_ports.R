# check-learner-ports, R side (plan.json design.check_learner_ports.r_calls).
#
# Usage: Rscript code/check_learner_ports.R <unit.csv> <seed> <out.csv>
#        Rscript code/check_learner_ports.R --versions <out.json>
#
# Sources the authors' ML_Functions.R (verbatim copy, never edited) and, for each learner in the
# order lasso, tree, forest, boosting, nnet, calls set.seed(<seed> + learner index 1..5) and fits
# the Y and D nuisance functions on each training fold of the synthetic unit, exactly as the
# authors' cond_comp() calls them with the arguments of 401K.R. Writes the out-of-fold
# predictions ($yhatout) with columns unit, fold, row, learner, l_hat, m_hat and, for the lasso,
# lambda0, n and p of both fits. Synthetic data only: the unit file holds the nine real covariates
# with a synthetic y and d; net_tfa and e401 are never read.

suppressPackageStartupMessages({
  library(hdm); library(rpart); library(randomForest); library(gbm); library(nnet); library(glmnet)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 2 && args[1] == "--versions") {
  pk <- c("hdm", "rpart", "randomForest", "gbm", "nnet", "glmnet")
  v <- sapply(pk, function(p) as.character(packageVersion(p)))
  v <- c(v, R = paste(R.version$major, R.version$minor, sep = "."))
  writeLines(paste0("{", paste0('"', names(v), '": "', v, '"', collapse = ", "), "}"), args[2])
  quit(save = "no", status = 0)
}
stopifnot(length(args) == 3)
unit_file <- args[1]; seed <- as.integer(args[2]); out_file <- args[3]

source("code/authors/ML_Functions.R")
options(warn = -1)  # as in the authors' 401K.R

dat  <- read.csv(unit_file)
cols <- c("y", "d", "age", "inc", "educ", "fsize", "marr", "twoearn", "db", "pira", "hown")

# 401K.R inputs
x  <- "age + inc + educ + fsize + marr + twoearn + db + pira + hown"
xl <- "(poly(age, 6, raw=TRUE) + poly(inc, 8, raw=TRUE) + poly(educ, 4, raw=TRUE) + poly(fsize, 2, raw=TRUE) + marr + twoearn + db + pira + hown)^2"
RLasso <- list(penalty = list(homoscedastic = FALSE, X.dependent.lambda = FALSE, lambda.start = NULL, c = 1.1), intercept = TRUE)
Forest <- list(ntree = 1000, na.action = na.omit, replace = TRUE)  # clas_/reg_nodesize removed, as cond_comp() does
opt    <- list(bag.fraction = .5, train.fraction = 1.0, interaction.depth = 2, n.trees = 1000, shrinkage = .01,
               n.cores = 1, cv.folds = 5, verbose = FALSE)        # clas_dist/reg_dist removed, as cond_comp() does
Nnet   <- list(size = 8, maxit = 1000, decay = 0.01, MaxNWts = 10000, trace = FALSE)

fit_pair <- function(learner, datause, dataout) {
  info <- c(lambda0_y = NA, n_y = NA, p_y = NA, lambda0_d = NA, n_d = NA, p_d = NA)
  if (learner == "lasso") {
    fy <- rlassoF(datause, dataout, xl, "y", post = FALSE, arg = RLasso)
    fd <- rlassoF(datause, dataout, xl, "d", post = FALSE, logit = TRUE, arg = RLasso)
    info <- c(lambda0_y = fy$model$lambda0, n_y = nrow(datause), p_y = length(fy$model$beta),
              lambda0_d = fd$model$lambda0, n_d = nrow(datause), p_d = length(fd$model$beta))
  } else if (learner == "tree") {
    fy <- tree(datause, dataout, x, "y", method = "anova", arg = list())
    fd <- tree(datause, dataout, x, "d", method = "class", arg = list())
  } else if (learner == "forest") {
    fy <- RF(datause, dataout, x, "y", nodesize = 5, arg = Forest, reg = TRUE)
    fd <- RF(datause, dataout, x, "d", nodesize = 1, arg = Forest, reg = TRUE)
  } else if (learner == "boosting") {
    fy <- boost(datause, dataout, x, "y", distribution = "gaussian", option = opt)
    fd <- boost(datause, dataout, x, "d", distribution = "adaboost", option = opt)
  } else if (learner == "nnet") {
    fy <- nnetF(datause, dataout, x, "y", arg = Nnet)
    fd <- nnetF(datause, dataout, x, "d", clas = TRUE, arg = Nnet)
  }
  list(l_hat = as.numeric(fy$yhatout), m_hat = as.numeric(fd$yhatout), info = info)
}

learners <- c("lasso", "tree", "forest", "boosting", "nnet")
out <- list()
for (li in seq_along(learners)) {
  set.seed(seed + li)
  for (f in sort(unique(dat$fold))) {
    datause <- dat[dat$fold != f, cols]
    dataout <- dat[dat$fold == f, cols]
    rownames(datause) <- NULL; rownames(dataout) <- NULL
    r <- fit_pair(learners[li], datause, dataout)
    out[[length(out) + 1]] <- data.frame(unit = dat$unit[1], fold = f, row = dat$row[dat$fold == f],
                                         learner = learners[li], l_hat = r$l_hat, m_hat = r$m_hat,
                                         t(r$info), check.names = FALSE)
  }
}
write.csv(do.call(rbind, out), out_file, row.names = FALSE)
