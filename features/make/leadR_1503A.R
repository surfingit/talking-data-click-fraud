#install.packages("fasttime")
rm(list=ls())
gc();gc();gc()
library(data.table)
library(RcppRoll)
library(fasttime)
library(Hmisc)


getLag = function(df, cols_, fname, path){
  df$click_sec = as.numeric(fasttime::fastPOSIXct(df$click_time))
  df$click_time = NULL
  df = df[,c(cols_, "click_sec"), with = F]
  df[, index := 1:nrow(df)]
  setorderv(df, c(cols_, "click_sec"))
  df[,click_sec_shift_lead := shift(click_sec, 1, type = "lead")]
  df[,click_sec_shift_lag  := shift(click_sec, 1, type = "lag")]
  df[,seq_lead := .N:1, by = .(ip, device, os) ]
  df[,seq_lag  := 1:.N, by = .(ip, device, os) ]
  df[,click_sec_lead := click_sec_shift_lead - click_sec]
  df[,click_sec_lag := click_sec - click_sec_shift_lag]
  df[seq_lead==1, click_sec_lead := -1]
  df[seq_lag==1,  click_sec_lag := -1]
  setorderv(df, "index")
  df[,.(click_sec_lead, click_sec_lag)]
  write.csv(df[,.(click_sec_lead, click_sec_lag)], 
            gzfile(paste0(path, fname)), 
            row.names = F, quote = F)
}


path = '~/tdata/data/'
path = '/Users/dhanley2/Documents/tdata/data/'

############################################
################ Lead & Lag ################
############################################

# Write out the <ip, device, os, channel, app> level
trndf = fread(paste0(path, 'train.csv'))
fname = "lead_lag_trn_ip_device_os_channel_app.gz"
cols_ = c("ip", "device", "os", "app", "channel")
getLag(trndf, cols_, fname, path)

tstdf = fread(paste0(path, 'test.csv'))
fname = "lead_lag_tst_ip_device_os_channel_app.gz"
cols_ = c("ip", "device", "os", "app", "channel")
getLag(tstdf, cols_, fname, path)

# Write out the <ip, device, os> level
trndf = fread(paste0(path, 'train.csv'))
fname = "lead_lag_trn_ip_device_os.gz"
cols_ = c("ip", "device", "os")
getLag(trndf, cols_, fname, path)

tstdf = fread(paste0(path, 'test.csv'))
fname = "lead_lag_tst_ip_device_os.gz"
cols_ = c("ip", "device", "os")
getLag(tstdf, cols_, fname, path)

  
# Write out the <ip, device, os, channel> level
trndf = fread(paste0(path, 'train.csv'))
fname = "lead_lag_trn_ip_device_os_channel.gz"
cols_ = c("ip", "device", "os", "channel")
getLag(trndf, cols_, fname, path)

tstdf = fread(paste0(path, 'test.csv'))
fname = "lead_lag_tst_ip_device_os_channel.gz"
cols_ = c("ip", "device", "os", "channel")
getLag(tstdf, cols_, fname, path)

############################################
########## Click Rolling Mean ##############
############################################

make_rmean = function(df, cols_, fname, path) {
  df$click_time = fasttime::fastPOSIXct(df$click_time)
  df$click_sec  = as.numeric(df$click_time)
  df$click_hr   = hour(df$click_time)
  df$click_day  = wday(df$click_time)
  df$click_time = NULL
  df = df[,c(cols_, "click_sec", "click_hr", "click_day"), with = F]
  df[, index := 1:nrow(df)]
  setorderv(df, c(cols_, "click_sec"))
  df[,count := length(click_sec), by = cols_ ]
  df[,count_hour := length(click_sec), by = c(cols_, "click_hr", "click_day") ]
  df[, click_sec_lead_hr := shift(click_sec, 1, type = "lead") - click_sec, by = c(cols_, "click_hr", "click_day") ]
  df[count_hour>=4,rmeanhr4 := roll_mean(click_sec_lead_hr, 4, align = "center"), by = c(cols_, "click_hr", "click_day")]
  df[count_hour>=40,rmeanhr40 := roll_mean(click_sec_lead_hr, 40, align = "center"), by = c(cols_, "click_hr", "click_day")]
  df[is.na(rmeanhr40), rmeanhr40 := -1]
  df[is.na(rmeanhr4 ), rmeanhr4  := -1]
  setorderv(df, "index")
  df = df[,.(count, count_hour, rmeanhr4, rmeanhr40)]
  gc()
  write.csv(df, gzfile(paste0(path, fname)), 
            row.names = F, quote = F)
}


# Write out the <ip, device, os, channel, app> level
trndf = fread(paste0(path, 'train.csv'))
fname = "../features/rmean_trn_device_os_app.gz"
cols_ = c("device", "os", "app")
make_rmean(trndf, cols_, fname, path)
rm(trndf)
gc()

# Write out the <ip, device, os, channel, app> level
tstdf = fread(paste0(path, 'test.csv'))
fname = "../features/rmean_tst_device_os_app.gz"
cols_ = c("device", "os", "app")
make_rmean(tstdf, cols_, fname, path)
rm(tstdf)
gc()