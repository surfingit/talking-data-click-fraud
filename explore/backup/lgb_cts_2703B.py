import pandas as pd
import time
import numpy as np
from sklearn.cross_validation import train_test_split
import lightgbm as lgb
import gc
from sklearn import metrics

def lgb_modelfit_nocv(params, dtrain, dvalid, predictors, target='target', objective='binary', metrics='auc',
                 feval=None, early_stopping_rounds=20, num_boost_round=3000, verbose_eval=10, categorical_features=None):
    lgb_params = {
        'boosting_type': 'gbdt',
        'objective': objective,
        'metric':metrics,
        'learning_rate': 0.01,
        #'is_unbalance': 'true',  #because training data is unbalance (replaced with scale_pos_weight)
        'num_leaves': 31,  # we should let it be smaller than 2^(max_depth)
        'max_depth': -1,  # -1 means no limit
        'min_child_samples': 20,  # Minimum number of data need in a child(min_data_in_leaf)
        'max_bin': 255,  # Number of bucketed bin for feature values
        'subsample': 0.6,  # Subsample ratio of the training instance.
        'subsample_freq': 0,  # frequence of subsample, <=0 means no enable
        'colsample_bytree': 0.3,  # Subsample ratio of columns when constructing each tree.
        'min_child_weight': 5,  # Minimum sum of instance weight(hessian) needed in a child(leaf)
        'subsample_for_bin': 200000,  # Number of samples for constructing bin
        'min_split_gain': 0,  # lambda_l1, lambda_l2 and min_gain_to_split to regularization
        'reg_alpha': 0,  # L1 regularization term on weights
        'reg_lambda': 0,  # L2 regularization term on weights
        'nthread': 16,
        'verbose': 0,
        'metric':metrics
    }

    lgb_params.update(params)

    print("preparing validation datasets")

    xgtrain = lgb.Dataset(dtrain[predictors].values, label=dtrain[target].values,
                          feature_name=predictors,
                          categorical_feature=categorical_features
                          )
    xgvalid = lgb.Dataset(dvalid[predictors].values, label=dvalid[target].values,
                          feature_name=predictors,
                          categorical_feature=categorical_features
                          )

    evals_results = {}

    bst1 = lgb.train(lgb_params, 
                     xgtrain, 
                     valid_sets=[xgtrain, xgvalid], 
                     valid_names=['train','valid'], 
                     evals_result=evals_results, 
                     num_boost_round=num_boost_round,
                     early_stopping_rounds=early_stopping_rounds,
                     verbose_eval=10, 
                     feval=feval)

    n_estimators = bst1.best_iteration
    print("\nModel Report")
    print("n_estimators : ", n_estimators)
    print(metrics+":", evals_results['valid'][metrics][n_estimators-1])

    return bst1

#path = '../input/'
path = "/home/darragh/tdata/data/"
path = '/Users/dhanley2/Documents/tdata/data/'
path = '/home/ubuntu/tdata/data/'
start_time = time.time()

dtypes = {
        'ip'            : 'uint32',
        'app'           : 'uint16',
        'device'        : 'uint16',
        'os'            : 'uint16',
        'channel'       : 'uint16',
        'is_attributed' : 'uint8',
        'click_id'      : 'uint32'
        }
ctdtypes = {
        'ip_app_channel_var_day'    : np.float32,
        'qty'                       : 'uint32',
        'ip_app_count'              : 'uint32',
        'ip_app_os_count'           : 'uint32',
        'qty_var'                   : np.float32,
        'ip_app_os_var'             : np.float32,
        'ip_app_channel_mean_hour'  : np.float32
        }

validation = False
if validation:
    add_ = 'val'
    ntrees = 200
    early_stop = 50
    test_usecols = ['ip','app','device','os', 'channel', 'click_time', 'is_attributed']
    val_size = 0
else:
    ntrees = 800
    val_size = 10000
    early_stop = ntrees
    add_ = ''
    test_usecols = ['ip','app','device','os', 'channel', 'click_time', 'click_id']

print('[{}] Load Train'.format(time.time() - start_time))
train_df = pd.read_csv(path+"train%s.csv"%(add_), dtype=dtypes, usecols=['ip','app','device','os', 'channel', 'click_time', 'is_attributed'])
print('[{}] Load Test'.format(time.time() - start_time))
test_df = pd.read_csv(path+"test%s.csv"%(add_), dtype=dtypes, usecols=test_usecols)

print('[{}] Load Features'.format(time.time() - start_time))
feattrnapp = pd.read_csv(path+'../features/lead_lag_trn_ip_device_os_app%s.gz'%(add_), compression = 'gzip')
feattstapp = pd.read_csv(path+'../features/lead_lag_tst_ip_device_os_app%s.gz'%(add_), compression = 'gzip')
feattrnspl = pd.read_csv(path+'../features/lead_split_sec_trn_ip_device_os_app%s.gz'%(add_), compression = 'gzip').astype(np.float32)
feattstspl = pd.read_csv(path+'../features/lead_split_sec_tst_ip_device_os_app%s.gz'%(add_), compression = 'gzip').astype(np.float32)
feattrnchl = pd.read_csv(path+'../features/lead_lag_trn_ip_device_os_channel%s.gz'%(add_), compression = 'gzip')
feattstchl = pd.read_csv(path+'../features/lead_lag_tst_ip_device_os_channel%s.gz'%(add_), compression = 'gzip')
feattrnos  = pd.read_csv(path+'../features/lead_lag_trn_ip_device_os%s.gz'%(add_), compression = 'gzip')
feattstos  = pd.read_csv(path+'../features/lead_lag_tst_ip_device_os%s.gz'%(add_), compression = 'gzip')
# feattrncum = pd.read_csv(path+'../features/cum_min_trn_ip_device_os_app%s.gz'%(add_), compression = 'gzip')
# feattstcum = pd.read_csv(path+'../features/cum_min_tst_ip_device_os_app%s.gz'%(add_), compression = 'gzip')
feattrnld2 = pd.read_csv(path+'../features/lead2_trn_ip_device_os_app%s.gz'%(add_), compression = 'gzip')
feattstld2 = pd.read_csv(path+'../features/lead2_tst_ip_device_os_app%s.gz'%(add_), compression = 'gzip')
feattrnnext  = pd.read_csv(path+'../features/next_trn_ip_device_os%s.gz'%(add_), compression = 'gzip').astype(np.int8)
feattstnext  = pd.read_csv(path+'../features/next_tst_ip_device_os%s.gz'%(add_), compression = 'gzip').astype(np.int8)
featentip  = pd.read_csv(path+'../features/entropyip.gz', compression = 'gzip')
featentip.iloc[:,1:] = featentip.iloc[:,1:].astype(np.float32)
featentip.iloc[:,0] = featentip.iloc[:,0].astype('uint32')


print('[{}] Finished Loading Features, start concatenate'.format(time.time() - start_time))
def sumfeat(df):
    dfsum = df.iloc[:,0] + df.iloc[:,1]
    dfsum[df.iloc[:,0]<0] = -1
    dfsum[df.iloc[:,1]<0] = -2
    dfsum[(df.iloc[:,1]>1000) & (df.iloc[:,0]>1000)] = -3
    dfsum[(df.iloc[:,1]<0) & (df.iloc[:,0]<0)] = -4
    return dfsum

feattstapp.columns = feattrnapp.columns = [i+'_app' for i in feattrnapp.columns.tolist()]
feattstchl.columns = feattrnchl.columns = [i+'_chl' for i in feattrnchl.columns.tolist()]
feattstos.columns  = feattrnos.columns  = [i+'_os' for i in feattrnos.columns.tolist()]

feattrn = pd.concat([feattrnchl, feattrnos, feattrnapp], axis=1)
feattst = pd.concat([feattstchl, feattstos, feattstapp], axis=1)
feattrn['click_sec_lsum_os'] = sumfeat(feattrnos)
feattrn['click_sec_lsum_chl'] = sumfeat(feattrnchl)
feattst['click_sec_lsum_os'] = sumfeat(feattstos)
feattst['click_sec_lsum_chl'] = sumfeat(feattstchl)
feattst[['click_sec_lead_chl', 'click_sec_lead_app']].head(300)
feattrn['click_sec_lead_sameappchl'] = \
        (feattrn['click_sec_lead_chl']==feattrn['click_sec_lead_app']).astype('int8')
feattst['click_sec_lead_sameappchl'] = \
        (feattst['click_sec_lead_chl']==feattst['click_sec_lead_app']).astype('int8')

del feattrnchl, feattrnos, feattrnapp
del feattstchl, feattstos, feattstapp
import gc
gc.collect()
#feattrn.hist()
#pd.crosstab(feattrn['click_sec_lag_sameappchl'],train_df['is_attributed'])#feattst.hist()

clip_val = 3600*9
feattrn = feattrn.clip(-clip_val, clip_val).astype(np.int32)
feattst = feattst.clip(-clip_val, clip_val).astype(np.int32)
feattrn = pd.concat([feattrn, feattrnld2, feattrnspl], axis=1)
feattst = pd.concat([feattst, feattstld2, feattstspl], axis=1)
del feattrnld2, feattrnspl
del feattstld2, feattstspl
gc.collect()
#feattrn.hist()
#feattst.hist()


print('Feat train/test shape...')
print(feattrn.shape)
print(feattst.shape)

print('Train/test shape...')
print(train_df.shape)
print(test_df.shape)


print('[{}] Concat Train/Test'.format(time.time() - start_time))
train_df = pd.concat([train_df, feattrn, feattrnnext], axis=1)
test_df  = pd.concat([test_df , feattst, feattstnext], axis=1)
del feattrn, feattst, feattrnnext, feattstnext
gc.collect()


print(train_df.shape)
print(test_df.shape)

len_train = len(train_df)
train_df=train_df.append(test_df)

del test_df
gc.collect()

print('[{}] Time prep'.format(time.time() - start_time))
train_df['hour'] = pd.to_datetime(train_df.click_time).dt.hour.astype('uint8')
train_df['day'] = pd.to_datetime(train_df.click_time).dt.day.astype('uint8')
train_df['minute'] = pd.to_datetime(train_df.click_time).dt.minute.astype('uint8')
gc.collect()


print('[{}] group by...unique app per ip/dev/os'.format(time.time() - start_time))
gp = train_df[['device', 'ip', 'os', 'app']].groupby(by=['device', 'ip', 'os'])[['app']].nunique().reset_index().rename(index=str, columns={'app': 'unique_app_ipdevos'})
print('merge...')
train_df = train_df.merge(gp[['device', 'ip', 'os', 'unique_app_ipdevos']], on=['device', 'ip', 'os'], how='left')
del gp
gc.collect()
train_df.rename(columns={'unique_app_ipdevos_x': 'unique_app_ipdevos'}, inplace = True)

print('[{}] group by...count app per ip/dev/os/min'.format(time.time() - start_time))
gp = train_df[['device', 'ip', 'os', 'app', 'minute']].groupby(by=['device', 'ip', 'os', 'minute'])[['app']].count().reset_index().rename(index=str, columns={'app': 'unique_app_ipdevosmin'})
print('merge...')
train_df = train_df.merge(gp[['device', 'ip', 'os', 'minute', 'unique_app_ipdevosmin']], on=['device', 'ip', 'os', 'minute'], how='left')
del gp
gc.collect()

print('[{}] group by...unique app per ip/day/hr/chl'.format(time.time() - start_time))
gp = train_df[['ip','day','hour','channel']].groupby(by=['ip','day','hour'])[['channel']].count().reset_index().rename(index=str, columns={'channel': 'qty'})
print('merge...')
train_df = train_df.merge(gp, on=['ip','day','hour'], how='left')
del gp
gc.collect()

print('[{}] group by...unique app per ip/app/chl'.format(time.time() - start_time))
gp = train_df[['ip','app', 'channel']].groupby(by=['ip', 'app'])[['channel']].count().reset_index().rename(index=str, columns={'channel': 'ip_app_count'})
train_df = train_df.merge(gp, on=['ip','app'], how='left')
del gp
gc.collect()


print('[{}] group by...unique app per ip/app/os/chl'.format(time.time() - start_time))
gp = train_df[['ip','app', 'os', 'channel']].groupby(by=['ip', 'app', 'os'])[['channel']].count().reset_index().rename(index=str, columns={'channel': 'ip_app_os_count'})
train_df = train_df.merge(gp, on=['ip','app', 'os'], how='left')
del gp
gc.collect()

print('[{}] Add entropy'.format(time.time() - start_time))
train_df = train_df.merge(featentip, on=['ip'], how='left')
train_df.head()

featentip.head()

print('[{}] Data types'.format(time.time() - start_time))
train_df['qty'] = train_df['qty'].astype('uint16')
train_df['ip_app_count'] = train_df['ip_app_count'].astype('uint16')
train_df['ip_app_os_count'] = train_df['ip_app_os_count'].astype('uint16')
train_df['click_sec_lead_shift2'] = train_df['click_sec_lead_shift2'].astype('int32')
#train_df['channel_app'] = train_df['channel'] + 500*train_df['app']
train_df.drop(['day', 'click_time' ,'unique_app_ipdevos'], axis = 1, inplace = True)
train_df.info()
gc.collect()

train_df.head(5)
print(train_df.shape)
test_df = train_df[len_train:]
val_df = train_df[(len_train-val_size):len_train]
train_df = train_df[:(len_train-val_size)]

gc.collect()

print('[{}] Get common train and test'.format(time.time() - start_time))
for col in ['app', 'channel', 'os', 'hour', 'device']:  
    gc.collect()
    print('Get common to train and test : %s'%(col))
    common = pd.Series(list(set(train_df[col]) & set(test_df[col])))
    train_df[col][~train_df[col].isin(common)] = np.nan
    test_df[col][~test_df[col].isin(common)] = np.nan
    val_df  [col][~val_df[col].isin(common)] = np.nan
    del common
    gc.collect()
for col in ['app', 'channel', 'os', 'hour', 'device']:
    train_df[col] = train_df[col].astype(np.float32)
    test_df [col] = test_df[col].astype(np.float32)
    val_df  [col] = val_df[col].astype(np.float32)
gc.collect()



print('[{}] Data split complete'.format(time.time() - start_time))
print("train size: ", len(train_df))
print("valid size: ", len(val_df))
print("test size : ", len(test_df))

lead_cols = [col for col in train_df.columns if 'lead_' in col]
lead_cols += [col for col in train_df.columns if 'lag_' in col]
lead_cols += [col for col in train_df.columns if 'next_' in col]
lead_cols += [col for col in train_df.columns if 'entropy' in col]
lead_cols += ['ip', 'app','device','os', 'channel', 'hour', 'qty', 'ip_app_count', 'ip_app_os_count', 'unique_app_ipdevosmin']
lead_cols = list(set(lead_cols))

target = 'is_attributed'
predictors =  lead_cols
categorical = [ 'app','device','os', 'channel', 'hour'] #'channel_app',
print(50*'*')
print(predictors)
print(50*'*')
print(categorical)
print(50*'*')

if not validation:
    train_df.drop(['click_id'], axis = 1, inplace = True)
    val_df.drop(['click_id'], axis = 1, inplace = True)
    sub = pd.DataFrame()
    sub['click_id'] = test_df['click_id'].astype('int')
else:
    val_df = test_df.sample(frac=0.025, replace=False, random_state=0)
    gc.collect()

    
print('[{}] Drop features complete'.format(time.time() - start_time))
print("train size: ", len(train_df))
print("valid size: ", len(val_df))
print("test size : ", len(test_df))

print('[{}] Training...'.format(time.time() - start_time))
params = {
    'learning_rate': 0.1,
    #'is_unbalance': 'true', # replaced with scale_pos_weight argument
    'num_leaves': 7,  # we should let it be smaller than 2^(max_depth)
    'max_depth': 3,  # -1 means no limit
    'min_child_samples': 100,  # Minimum number of data need in a child(min_data_in_leaf)
    'max_bin': 100,  # Number of bucketed bin for feature values
    'subsample': 0.7,  # Subsample ratio of the training instance.
    'subsample_freq': 1,  # frequence of subsample, <=0 means no enable
    'colsample_bytree': 0.7,  # Subsample ratio of columns when constructing each tree.
    'min_child_weight': 0,  # Minimum sum of instance weight(hessian) needed in a child(leaf)
    'scale_pos_weight':99 # because training data is extremely unbalanced 
}


bst = lgb_modelfit_nocv(params, 
                        train_df, 
                        val_df, 
                        predictors, 
                        target, 
                        objective='binary', 
                        metrics='auc',
                        early_stopping_rounds=early_stop, 
                        verbose_eval=True, 
                        num_boost_round=ntrees, 
                        categorical_features=categorical)

# [20]    train's auc: 0.973256   valid's auc: 0.967426
# [50]    train's auc: 0.980096   valid's auc: 0.975396
# [100]   train's auc: 0.984011   valid's auc: 0.979477
# [200]   train's auc: 0.985963   valid's auc: 0.98142


gc.collect()
imp = pd.DataFrame([(a,b) for (a,b) in zip(bst.feature_name(), bst.feature_importance())], columns = ['feat', 'imp'])
imp = imp.sort_values('imp', ascending = False).reset_index(drop=True)
print(imp)

if not validation:
    print("Predicting...")
    sub['is_attributed'] = bst.predict(test_df[predictors])
    print("writing...")
    sub.to_csv(path + '../sub/sub_lgb2703.csv.gz',index=False, compression = 'gzip')
    print("done...")
    print(sub.info())
else:
    max_ip = 126413
    preds =   bst.predict(test_df[predictors])
    fpr, tpr, thresholds = metrics.roc_curve(test_df['is_attributed'].values, preds, pos_label=1)
    print('Auc for all hours in testval : %s'%(metrics.auc(fpr, tpr)))
    idx = test_df['ip']<=max_ip
    fpr1, tpr1, thresholds1 = metrics.roc_curve(test_df[idx]['is_attributed'].values, preds[idx], pos_label=1)
    print('Auc for select hours in testval : %s'%(metrics.auc(fpr1, tpr1)))


'''
Without channel app
Auc for all hours in testval : 0.98135282046753
Auc for select hours in testval : 0.9631544908471926
'''

'''
Auc for all hours in testval : 0.9810998331513668
Auc for select hours in testval : 0.9625975906187854
'''
'''
# Split sec lead app
Auc for all hours in testval : 0.9809818567872455
Auc for select hours in testval : 0.9622151446259039
'''

'''
# Click sec lead of app
Auc for all hours in testval : 0.980384724718358
Auc for select hours in testval : 0.9613318834326467
'''

'''
# Click sec lead of app
Auc for all hours in testval : 0.9802027274200331
Auc for select hours in testval : 0.9608878940255907
'''

#                     feat  imp
#0                 channel_app  321
#1                          os  141
#2    click_sec_lead_split_sec  133
#3                     channel  112
#4                         qty   77
#5                         app   69
#6          click_sec_lead_app   52
#7        ip_click_min_entropy   42
#8                        hour   37
#9                      device   27
#10          ip_device_entropy   24
#11         ip_channel_entropy   23
#12        ip_click_hr_entropy   23
#13              ip_os_entropy   21
#14            ip_app_os_count   21
#15             ip_app_entropy   20
#16      click_sec_lead_shift2   14
#17          click_sec_lag_app   11
#18                         ip    8
#19         click_sec_lead_chl    7
#20               ip_app_count    6
#21          click_sec_lead_os    4
#22              same_next_app    3
#23          click_sec_lag_chl    3
#24  click_sec_lead_sameappchl    1
#25              same_next_chl    0
