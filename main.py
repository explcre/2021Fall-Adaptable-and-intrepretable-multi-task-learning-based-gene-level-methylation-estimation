# -*- coding : utf-8-*-
# coding:unicode_escape
import pandas as pd
import numpy as np
import sklearn
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, LinearRegression
import sklearn.naive_bayes as bayes
from sklearn.ensemble import AdaBoostClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier

from train_keras_redefined_loss import run
from predict_keras_redefined_loss import predict

KnnMod = KNeighborsClassifier()
LrMod = LogisticRegression()
BayesBernlliMod = bayes.BernoulliNB(alpha=1.0,binarize=0.0,fit_prior=True,class_prior=None)
BayesGaussianMod = bayes.GaussianNB()
DecisionTreeMod = DecisionTreeClassifier(
    criterion='entropy',
    max_depth=None,min_samples_split=2,
    min_samples_leaf=1,max_features=None
    )

SvmMod = SVC(probability=True)
adaMod = AdaBoostClassifier(base_estimator=None)
gbMod = GradientBoostingClassifier(loss='deviance', learning_rate=0.1, n_estimators=200, subsample=1.0,
                                   min_samples_split=2, min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_depth=3,
                                   init=None, random_state=None, max_features=None, verbose=0)
rfMod = RandomForestClassifier(n_estimators=100, criterion='gini', max_depth=None, min_samples_split=2,
                               min_samples_leaf=1, min_weight_fraction_leaf=0.0, max_features='auto',
                               max_leaf_nodes=None, bootstrap=True, oob_score=False, n_jobs=1, random_state=None,
                               verbose=0)
LinRegMod = LinearRegression(fit_intercept=True,normalize=False,copy_X=True,n_jobs=1)
mod_list = [LinRegMod,KnnMod, LrMod,BayesBernlliMod,BayesGaussianMod,DecisionTreeMod, SvmMod, adaMod, gbMod, rfMod]

def crossDict(functions,train_x,train_y ,cv,verbose,scr,test_x,test_y):
    valDict={}
    for func in functions:
        valScore = cross_val_score(func,train_x,train_y,cv=cv,verbose=verbose,scoring=scr)
        func.fit(train_x,train_y)
        testScore = func.score(test_x,test_y)
        valDict[str(func).split('(')[0]] = [valScore.mean(), valScore.std(),testScore]
    return valDict

#############################################
justToCheckBaseline=False
toFillPoint5=True
toMask=True
framework='pytorch'
'''
if framework=='keras':
    from train_keras_redefined_loss import run
    from predict_keras_redefined_loss import predict
elif framework=='pytorch':
    from train_pytorch import run
    from predict_pytorch import predict
'''
# from test import select_feature
import torch

torch.set_printoptions(profile="full")
# from torchsummary import summary

platform = "platform.json"
model_type = "AE"  # "RandomForest"
predict_model_type = "L2"
data_type = "origin_data"
dataset_type = "train"
isTrain = True
toTrainAE = True
toTrainNN = True
isPredict = True
toTrainMeiNN = True
toAddGeneSite = True
toAddGenePathway = True
just_check_data = False

onlyGetPredictionFromLocalAndCheckAccuracy = False
lossMode = 'reg_mean'
# reg_mean: we set loss as mean of regularization+prediction loss
# auto_scale:
# no:no mode
selectNumResidueMode = 'num'
# num:define num of selected residue
# pvalue:define a threshold of pvalue
# min: index will be minimum of 1,num_of_selected and 2.(last index pvalue which < pvalueThreshold)
pvalueThreshold = 1e-5
num_of_selected_residue = 1000
selectNumPathwayMode = 'equal_difference'  # '=num_gene'
# '=num_gene': equal number of gene selected
# 'equal_difference': make pathway-gene-residue an arithmetic sequence
# 'num' : give a value
num_of_selected_pathway = num_of_selected_residue / 2
isMultiDataset = True
multiDatasetMode = "multi-task" #'multi-task'
# 'softmax': multi-class, with last layer of MeiNN is softmax
# 'multi-task': multi-task solution with network architecture for each task
# 'pretrain-finetune': first pretrain a big model with multi-tasks, then finetune each single dataset classifier
datasetNameList = ['diabetes1', 'IBD', 'MS', 'Psoriasis', 'RA','SLE']  # "diabetes1","RA","Psoriasis"]#,"RA","Psoriasis"]#,"Psoriasis","IBD"]# ['diabetes1','Psoriasis','SLE']
model = None
AE_epoch = 100  # *len(datasetNameList)
NN_epoch = 100  # *len(datasetNameList)
separatelyTrainAE_NN = False
toAddSkipConnection = False
ae = None
fcn = None
myMeiNN = None

code = ''
for i in datasetNameList:
    code += (i + '-')  # "GSE66695"#GSE42861_processed_methylation_matrix #"GSE66695-series"
num_of_selected_residue_list = [2000, 2000, 2000]
h_dim = 60 * len(datasetNameList)
date = '7-21p-base-m-pd0000-f0%sAep%d-Nep%d-Site%sPath%s-res%d-lMod-%s-sep%s-%s-pMd%s' % (
    (len(datasetNameList) > 1), AE_epoch, NN_epoch, toAddGeneSite, toAddGenePathway, num_of_selected_residue, lossMode,
    separatelyTrainAE_NN, multiDatasetMode,selectNumPathwayMode)
keras = True
path = r"./result/"
selected_residue_name_list = set()


# filename_dict = {'small': "./dataset/data_train.txt"}


def binearySearch_df(df, threshold):
    # pvaluePos=0
    left = 0
    right = len(df) - 1
    while left < right:
        middle = int(left + (right - left) / 2)
        if df.iloc[middle, -1] >= threshold:
            right = middle - 1
        elif df.iloc[middle, -1] < threshold:  # avoid infinte loop
            if left == middle:
                if df.iloc[right, -1] < threshold:
                    left = right
                break
            else:
                left = middle  # keep index < threshold incase it's last one
    '''two possibility if jump out of loop
    1.break???at this time left == right
    2.left == right
    3.left > right???when all element >=threshold,at this time left == 0 & & right == -1'''
    if df.iloc[left, -1] < threshold:
        return left
    else:
        return -1
    # return pvaluePos


def data_preprocessing(data_train, isMultiDataset=False, datasetNameList=[''], index=0,
                       selected_residue_name_list=set()):
    y_train = data_train.iloc[:, -1].T
    data_train = data_train.iloc[:, :-1].T

    data_train_df = pd.DataFrame(data_train)
    print("data_train_df=")
    print(data_train_df)
    print("y_train")
    print(y_train)
    if datasetNameList[0] == "GSE66695" and len(datasetNameList) == 1:
        data_label_df0 = pd.DataFrame(y_train, columns=['Ground Truth'], index=data_train_df.columns)
    else:
        data_label_df0 = pd.DataFrame(y_train,
                                      columns=['Ground Truth' + datasetNameList[index]])  # datasetNameList[index]+
        # data_label_df0.rename(columns={'Ground Truth':datasetNameList[index]+'Ground Truth'})
        # data_label_df0['Ground Truth'].rename(datasetNameList[index]+'Ground Truth')
    data_label_df = data_label_df0.T

    print("data_label_df=")
    print(data_label_df)
    data_train_label_df = data_train_df.append(data_label_df)  # pd.concat([data_train_df, data_label_df], axis=0)
    print("after join data and label")
    print(data_train_label_df)
    from scipy import stats
    data_train_label_df_T = data_train_label_df.T
    print("data_train_label_df_T[data_train_label_df_T['Ground Truth%s']==1.0]" % datasetNameList[index])

    print(data_train_label_df_T[data_train_label_df_T['Ground Truth' + datasetNameList[index]] == 1.0])
    t_test_result = stats.ttest_ind(
        data_train_label_df_T[data_train_label_df_T['Ground Truth' + datasetNameList[index]] == 1.0],
        data_train_label_df_T[data_train_label_df_T['Ground Truth' + datasetNameList[index]] == 0.0])

    print("t_testresult=")
    print(t_test_result)
    print("t_testresult.pvalue=")
    print(t_test_result.pvalue)
    print("t_testresult.pvalue.shape=")
    print(t_test_result.pvalue.shape)

    data_train_label_df[datasetNameList[index] + ' pvalue'] = t_test_result.pvalue

    print("data_train_label_df added pvalue")
    print(data_train_label_df)
    print("t_testresult.pvalue.sort()=")
    print(np.sort(t_test_result.pvalue))
    print("data_train_label_df.sort_values(by='pvalue',ascending=True)")

    data_train_label_df_sorted_by_pvalue = data_train_label_df.sort_values(by=datasetNameList[index] + ' pvalue',
                                                                           ascending=True)

    print(data_train_label_df_sorted_by_pvalue)
    print("data_train_label_df_sorted_by_pvalue.iloc[1:,:-1])")
    data_train_label_df_sorted_by_pvalue_raw = data_train_label_df_sorted_by_pvalue.iloc[:, :-1]  # [1:, :-1]
    print(data_train_label_df_sorted_by_pvalue_raw)
    if selectNumResidueMode == 'num':
        selected_residue_train_data = data_train_label_df_sorted_by_pvalue_raw.iloc[:num_of_selected_residue + 1, :]
    elif selectNumResidueMode == 'pvalue' or selectNumResidueMode == 'min':
        pvaluePos = binearySearch_df(data_train_label_df_sorted_by_pvalue, pvalueThreshold)
        if not pvaluePos == -1:
            selected_residue_train_data = data_train_label_df_sorted_by_pvalue_raw.iloc[:pvaluePos, :]
        else:
            raise Exception("ERROR: Cannot find position which satisfies pvalue threshold!")
        if selectNumResidueMode == 'min':
            min_of_selected_index = min(num_of_selected_residue + 1, pvaluePos)
            selected_residue_train_data = data_train_label_df_sorted_by_pvalue_raw.iloc[:min_of_selected_index, :]
    else:
        raise Exception("ERROR: selectResidueMode can only be num or pvalue")

    print("selected_residue_train_data)")
    print(selected_residue_train_data)
    if index == 0:
        selected_residue_name_list = set('')
    selected_residue_name_list = selected_residue_name_list.union(
        set(selected_residue_train_data.index.values.tolist()))
    print("selected_residue_name_list")
    print(selected_residue_name_list)
    selected_residue_train_data = selected_residue_train_data.sort_index(ascending=True)
    print("selected_residue_train_data(sorted by index)")
    print(selected_residue_train_data)
    data_train = selected_residue_train_data

    return data_train, selected_residue_name_list


train_dataset_filename_list = []
train_label_filename_list = []
test_dataset_filename_list = []
test_label_filename_list = []

if len(datasetNameList) > 0 and (not datasetNameList[0] == "GSE66695"):
    isSelfCollectedDataset = True
    for i, datasetName in enumerate(datasetNameList):
        train_dataset_filename_list.append(r"./dataset/" + datasetNameList[
            i] + "/beta_value.csv")  # "./dataset/data_train.txt"#"./dataset/diabetes1/beta_value.csv"#"./dataset/data_train.txt"# GSE66695_series_matrix.txt"#r"./dataset/data_train.txt"#GSE42861_processed_methylation_matrix.txt
        train_label_filename_list.append(r"./dataset/" + datasetNameList[
            i] + "/label.csv")  # "./dataset/label_train.txt"#"./dataset/diabetes1/label.csv"#"./dataset/label_train.txt"
        test_dataset_filename_list.append(r"./dataset/" + datasetNameList[
            i] + "/beta_value.csv")  # "./dataset/data_test.txt"#"./dataset/diabetes1/beta_value.csv"#"./dataset/data_test.txt"
        test_label_filename_list.append(r"./dataset/" + datasetNameList[
            i] + "/label.csv")  # "./dataset/label_test.txt"#"./dataset/diabetes1/label.csv"#"./dataset/label_test.txt"
elif len(datasetNameList) > 0:
    isSelfCollectedDataset = False
    train_dataset_filename_list.append(
        r"./dataset/data_train.txt")  # "./dataset/diabetes1/beta_value.csv"#"./dataset/data_train.txt"# GSE66695_series_matrix.txt"#r"./dataset/data_train.txt"#GSE42861_processed_methylation_matrix.txt
    train_label_filename_list.append(
        r"./dataset/label_train.txt")  # "./dataset/diabetes1/label.csv"#"./dataset/label_train.txt"
    test_dataset_filename_list.append(
        r"./dataset/data_test.txt")  # "./dataset/diabetes1/beta_value.csv"#"./dataset/data_test.txt"
    test_label_filename_list.append(r"./dataset/label_test.txt")  #
else:
    raise Exception("ERROR: datasetNameList is empty")

'''
def print_model_summary_pytorch():
    print('###############################################################')
    file = open(date + "ae_detail.csv", mode='w', encoding='utf-8')
    model_ae=torch.load(date+'_auto-encoder.pth')
    summary(model_ae,input_size=(0,809))#, input_size=(3, 512, 512)
    #file.write(summary(model_ae,input_size=(0,809)))
    print(model_ae)
    for name,parameters in model_ae.named_parameters():
        print(name+':'+str(parameters.size()))
        print(parameters)

        file.write(name+':'+str(parameters.size()))
        file.write(str(parameters))
    print('###############################################################')
'''
toCheckHeatMap=False
if toCheckHeatMap:
    from keras import backend as K, losses
    from keras.models import load_model
    def relu_advanced(x):
        return K.relu(x, threshold=0)
    def myLoss(y_true, y_pred):
        return losses.binary_crossentropy(y_true, y_pred)
    loaded_fcn_multitask=load_model(path + date + 'multi-task-MeiNN.h5'
                                            ,custom_objects={'relu_advanced': relu_advanced, 'myLoss': myLoss})
    print("loaded_fcn_multitask")
    print(loaded_fcn_multitask.summary())
    import seaborn as sns
    import matplotlib.pylab as plt
    plt.figure(figsize=(10,10))
    weight=loaded_fcn_multitask.get_weights()
    layer_gene_pathway=12
    heat_map_gene_pathway = sns.heatmap( weight[layer_gene_pathway], linewidth = 1 , annot = False)
    plt.title(path + date + 'multi-task-MeiNN gene-pathway HeatMap' )
    plt.savefig(path + date + 'multi-task-MeiNN_gene_pathway_heatmap.png')
    plt.show()

    heat_map_gene_pathway_clustered = sns.clustermap( weight[layer_gene_pathway],row_cluster=True,standard_scale=1)
    plt.title(path + date + 'multi-task-MeiNN gene-pathway row-clustered cluster Map' )
    plt.savefig(path + date + 'multi-task-MeiNN_gene_pathway_row-clustered_cluster_map.png')
    plt.show()

    layer_gene_site=15
    heat_map_gene_site = sns.heatmap( list(weight[layer_gene_site]), linewidth = 1 , annot = False)
    plt.title(path + date + 'multi-task-MeiNN gene-site HeatMap' )
    plt.savefig(path + date + 'multi-task-MeiNN_gene_site_heatmap.png')
    plt.show()

# train
if True or isTrain:
    # train_data = pd.read_excel(train_dataset_filename,skiprows=30)#, index_col=0,names=['0','1']#,delimiter='!|\t'
    # train_data['0'].str.split('\t', expand=True)
    if isSelfCollectedDataset and (not isMultiDataset):

        train_data_total = pd.read_csv(train_dataset_filename_list[0], index_col=0)  # ,skiprows=30,delimiter='\t')
        train_label_total_csv = pd.read_csv(train_label_filename_list[0], index_col=0)  # .values.ravel()
        train_label_total_csv_df = pd.DataFrame(train_label_total_csv)
        train_data_and_label_df = pd.concat([train_data_total, train_label_total_csv_df.T], axis=0)

        train_data_and_label_df = data_preprocessing(train_data_and_label_df.T)
        train_data, test_data = train_test_split(train_data_and_label_df.T, train_size=0.75, random_state=10)

        train_label = train_data.iloc[:, 0].T  # train_data.iloc[:,-1].T
        test_label = test_data.iloc[:, 0].T  # test_data.iloc[:,-1].T
        train_data = train_data.iloc[:, 1:].T  # train_data.iloc[:, :-1].T
        test_data = test_data.iloc[:, 1:].T  # test_data.iloc[:, :-1].T
        print("train_data_and_label_df")
        print(train_data_and_label_df)

        print("read train_data_total.shape:")
        print(train_data_total.shape)
        print(train_data_total)

        print("finish read train data")
        # train_data,test_data=train_test_split(train_data_total, train_size=0.75, random_state=10)
        print("train_data_splited.shape:")
        print(train_data.shape)
        print(train_data)
        print("test_data_splited.shape:")
        print(test_data.shape)
        print(test_data)
        print("train_label_splited.shape:")
        print(train_label.shape)
        print(train_label)
        print("test_label_splited.shape:")
        print(test_label.shape)
        print(test_label)
        '''
        train_label_total = pd.read_csv(train_label_filename, index_col=0).values.ravel()
        train_label_total_csv=pd.read_csv(train_label_filename,index_col=0)
        train_label_total_df=pd.DataFrame(train_label_total)
        print("finish read train label total")
        print(train_label_total)
        print("train_label_total_df")
        print(train_label_total_df)
        print("train_label_total_csv")
        print(train_label_total_csv)
        train_label, test_label = train_test_split(train_label_total_csv, train_size=0.75, random_state=10)
        '''
    elif isSelfCollectedDataset and isMultiDataset:
        import os

        if False and os.path.exists(path + date + "_" + code + str(len(datasetNameList)) + "-th multi_df).txt",):
            multi_train_data_and_label_df = pd.read_csv(
                        path + date + "_" + code + str(len(datasetNameList)) + "-th multi_df).txt",
                sep='\t')
            print(
                "we finish reading " + path + date + "_" + code + str(len(datasetNameList)) + "-th multi_df).txt")
        else:
            for i, dataset_name in enumerate(datasetNameList):
                if i > 0:
                    # train_data_total = pd.read_csv(train_dataset_filename_list[i-1], index_col=0)
                    train_data_total_last = pd.read_csv(train_dataset_filename_list[i - 1],
                                                        index_col=0)  # ,skiprows=30,delimiter='\t')
                    train_label_total_csv_last = pd.read_csv(train_label_filename_list[i - 1],
                                                             index_col=0)  # .values.ravel()
                    train_label_total_csv_df_last = pd.DataFrame(train_label_total_csv_last)
                    last_full_df = pd.concat([train_data_total_last, train_label_total_csv_df_last.T], axis=0)
                train_data_total = pd.read_csv(train_dataset_filename_list[i],
                                               index_col=0)  # ,skiprows=30,delimiter='\t')
                train_label_total_csv = pd.read_csv(train_label_filename_list[i], index_col=0)  # .values.ravel()
                train_label_total_csv_df = pd.DataFrame(train_label_total_csv)
                train_data_and_label_df_full = pd.concat([train_data_total, train_label_total_csv_df.T], axis=0)

                train_data_and_label_df, selected_residue_name_list = data_preprocessing(train_data_and_label_df_full.T,
                                                                                         isMultiDataset,
                                                                                         datasetNameList, i,
                                                                                         selected_residue_name_list)

                print("%d-th %s train_data_and_label_df" % (i, dataset_name))
                print(train_data_and_label_df)

                print("%d-th %s read train_data_total.shape:" % (i, dataset_name))
                print(train_data_total.shape)
                print(train_data_total)
                if i == 0:
                    multi_train_data_and_label_df = train_data_and_label_df
                    multi_train_data_and_label_df.to_csv(
                        path + date + "_" + code + str(
                            i) + "-th multi_df).txt",
                        sep='\t')
                else:
                    print("last_full_df.loc[list(intersection_of_residue)]")
                    indexset = set(last_full_df.index.values.tolist())
                    intersection_of_residue = indexset.intersection(selected_residue_name_list)
                    intersection_of_residue_minus_existed = intersection_of_residue.difference(
                        set(multi_train_data_and_label_df.index.values.tolist()))
                    last_df_with_selected_residue = last_full_df.loc[list(intersection_of_residue_minus_existed)]
                    print(last_df_with_selected_residue)
                    multi_train_data_and_label_df = pd.concat(
                        [multi_train_data_and_label_df, last_df_with_selected_residue], axis=0)
                    print("after 1st concat multi_train_data_and_label_df")
                    print(multi_train_data_and_label_df)

                    indexset_now = set(train_data_and_label_df_full.index.values.tolist())
                    # print("indexset_now")
                    # print(indexset_now)
                    intersection_of_residue_now = indexset_now.intersection(selected_residue_name_list)
                    # print("intersection_of_residue_now")
                    # print(intersection_of_residue_now)
                    intersection_of_residue_minus_existed_now = intersection_of_residue_now.difference(
                        set(train_data_and_label_df.index.values.tolist()))
                    # print("intersection_of_residue_minus_existed_now")
                    # print(intersection_of_residue_minus_existed_now)
                    last_df_with_selected_residue_now = train_data_and_label_df_full.loc[
                        list(intersection_of_residue_minus_existed_now)]
                    print("intersection_of_residue_minus_existed_now")
                    print(last_df_with_selected_residue_now)
                    train_data_and_label_df_now = pd.concat(
                        [train_data_and_label_df, last_df_with_selected_residue_now], axis=0)
                    print("after 2st concat train_data_and_label_df_now")
                    print(train_data_and_label_df_now)

                    multi_train_data_and_label_df = pd.concat(
                        [multi_train_data_and_label_df, train_data_and_label_df_now], axis=1)

                    print("%d-th %s multi preprocessed train data:" % (i, dataset_name))
                    print(multi_train_data_and_label_df)
                    multi_train_data_and_label_df.to_csv(
                        path + date + "_" + code + str(
                            i) + "-th multi_df).txt",
                        sep='\t')

        multi_train_data_and_label_df = multi_train_data_and_label_df.sort_index(ascending=True)
        print("after sort multi_train_data_and_label_df")
        print(multi_train_data_and_label_df)
        if not toFillPoint5:
            multi_train_data_and_label_df = multi_train_data_and_label_df.fillna(0.0)
        else:
            multi_train_data_and_label_df.iloc[:max(0, len(datasetNameList) - 1) + 1,:] = multi_train_data_and_label_df.iloc[:max(0, len(datasetNameList) - 1) + 1,:].fillna(0.5)#0.5
            multi_train_data_and_label_df.iloc[max(1, len(datasetNameList)):,:] = multi_train_data_and_label_df.iloc[max(1, len(datasetNameList)):,:].fillna(0.0)
        print("after sort and fill nan multi_train_data_and_label_df")
        print(multi_train_data_and_label_df)
        train_data, test_data = train_test_split(multi_train_data_and_label_df.T, train_size=0.75, random_state=10)

        train_label = train_data.iloc[:, :max(0, len(datasetNameList) - 1) + 1].T  # train_data.iloc[:,-1].T
        test_label = test_data.iloc[:, :max(0, len(datasetNameList) - 1) + 1].T  # test_data.iloc[:,-1].T
        train_data = train_data.iloc[:, max(1, len(datasetNameList)):].T  # train_data.iloc[:, :-1].T
        test_data = test_data.iloc[:, max(1, len(datasetNameList)):].T  # test_data.iloc[:, :-1].T

        print("finish read train data")
        # train_data,test_data=train_test_split(train_data_total, train_size=0.75, random_state=10)
        print("train_data_splited.shape:")
        print(train_data.shape)
        print(train_data)
        print("test_data_splited.shape:")
        print(test_data.shape)
        print(test_data)
        print("train_label_splited.shape:")
        print(train_label.shape)
        print(train_label)
        print("test_label_splited.shape:")
        print(test_label.shape)
        print(test_label)
    elif not isSelfCollectedDataset:
        train_data = pd.read_table(train_dataset_filename_list[0], index_col=0)
        print("read train_data.shape:")
        print(train_data.shape)
        print(train_data[0:15])
        train_data.head(10)
        print("finish read train data")
        train_label = pd.read_table(train_label_filename_list[0], index_col=0).values.ravel()
        print("finish read train label")
        print(train_data.head(10))
        test_data = pd.read_table(test_dataset_filename_list[0], index_col=0)
        test_label = pd.read_table(test_label_filename_list[0], index_col=0)

if isTrain:
    if (not just_check_data):
        if (framework=='keras' or framework=='pytorch') and toTrainMeiNN == True:
            ############2022-7-16baseline building############################
            if justToCheckBaseline:
                csd = crossDict(mod_list, train_data.T, train_label.T, 9, 1, "accuracy",test_data.T,test_label.T)
                print("*"*20+"baseline models"+"*"*20)
                print(datasetNameList)
                print("%d"%num_of_selected_residue)
                f = open(path+date+"baseline_model_results.txt", 'w')
                print(csd)
            ##################################################################
            if not justToCheckBaseline:
                myMeiNN, residue_name_list = run(path, date, code, train_data, train_label, platform, model_type, data_type,
                                             h_dim,
                                             toTrainMeiNN=toTrainMeiNN, toAddGenePathway=toAddGenePathway,
                                             toAddGeneSite=toAddGeneSite, multiDatasetMode=multiDatasetMode,
                                             datasetNameList=datasetNameList,
                                             num_of_selected_residue=num_of_selected_residue,
                                             lossMode=lossMode, selectNumPathwayMode=selectNumPathwayMode,
                                             num_of_selected_pathway=num_of_selected_pathway,
                                             AE_epoch_from_main=AE_epoch, NN_epoch_from_main=NN_epoch,
                                             separatelyTrainAE_NN=separatelyTrainAE_NN,toMask=toMask,framework=framework)
            if framework=='keras':
                myMeiNN.fcn.summary()
                myMeiNN.autoencoder.summary()
            elif framework == 'pytorch':
                #print(myMeiNN)
                pass
        elif (toTrainMeiNN == False):
            (ae, fcn) = run(path, date, code, train_data, train_label, platform, model_type, data_type, h_dim,
                            toTrainAE, AE_epoch, NN_epoch)
            ae.summary()
            fcn.summary()
        else:
            run(path, date, code, train_data, train_label, platform, model_type, data_type, h_dim, toTrainAE, toTrainNN,
                AE_epoch, NN_epoch)
'''
if keras:
    ae.summary()
    fcn.summary()
'''
if not justToCheckBaseline:
    residue_name_list = np.load(
        path + date + "_" + code + "_gene_level" + "_original_residue_name_list)" + ".txt.npy")

print("test label is")
print(test_label)
# test_label = pd.DataFrame(np.array(test_label)))
test_label.T.to_csv(
    path + date + "_" + code + "test_label).txt",
    sep='\t')

# predict
if isPredict and (not just_check_data) and (not onlyGetPredictionFromLocalAndCheckAccuracy) and (not justToCheckBaseline):
    # test_data = pd.read_table(test_dataset_filename, index_col=0)
    # test_label = pd.read_table(test_label_filename, index_col=0)
    '''
    predict(path, date, code, test_data, test_label, platform,
            date + "_" + code + "_" + model_type + "_" + data_type + dataset_type + "_model.pickle", model_type,
            data_type, model, predict_model_type, residue_name_list, datasetNameList=multi_train_data_and_label_df,
            separatelyTrainAE_NN=separatelyTrainAE_NN,multiDatasetMode=multiDatasetMode,framework=framework)'''
    predict(path, date, code, test_data, test_label, platform,date + "_" + code + "_" + model_type + "_" + data_type + dataset_type + "_model.pickle",
            model_type, data_type,h_dim,toTrainMeiNN,model,predict_model_type, residue_name_list,
            toAddGenePathway=toAddGenePathway,
            toAddGeneSite=toAddGeneSite, multiDatasetMode=multiDatasetMode,
            datasetNameList=datasetNameList,
            num_of_selected_residue=num_of_selected_residue,
            lossMode=lossMode, selectNumPathwayMode=selectNumPathwayMode,
            num_of_selected_pathway=num_of_selected_pathway,
            AE_epoch_from_main=AE_epoch, NN_epoch_from_main=NN_epoch,
            separatelyTrainAE_NN=separatelyTrainAE_NN, framework=framework)
elif isPredict and (not just_check_data) and (onlyGetPredictionFromLocalAndCheckAccuracy) and (not justToCheckBaseline):
    data_test_pred = pd.read_csv(
        path + date + "_" + code + "_gene_level" + "(" + data_type + '_' + model_type + ").txt",
        sep='\t', index_col=0)
    print("data_test_pred=")
    print(data_test_pred)
    num_wrong_pred = 0
    normalized_pred_out = pd.read_csv(
        path + date + "_" + code + "_gene_level" + "(" + data_type + '_' + model_type + "normalized_pred).txt",
        sep='\t', index_col=0)
    print("normalized pred_out=")
    print(normalized_pred_out)
    for i, item in enumerate(normalized_pred_out.index):
        print("i:%d" % i)
        num_wrong_pred += round(abs(test_label.iloc[int(i)] - int(normalized_pred_out.iloc[int(i)])))

    print("test label is")
    print(test_label)
    print("num_wrong_pred=%d, total test num=%d,accuracy=%f" % (
        num_wrong_pred, len(test_label), 1.0 - num_wrong_pred / len(test_label)))

    '''print("normalized pred_out=")
    print(normalized_pred_out)
    print("test label is")
    print(gene_data_test)
    print("num_wrong_pred=%d, total test num=%d,accuracy=%f" % (
    num_wrong_pred, len(gene_data_test), 1.0 - num_wrong_pred / len(gene_data_test)))
    print(gene_data_test[i])'''

'''
# test(feature selection)
data = pd.read_table(r"./dataset/"+date+"_"+code+"_gene_level("+data_type+"_"+model_type+").txt", index_col=0)
label = pd.read_table(test_label_filename, index_col=0).values.ravel()
'''
# select_feature(code, data, label, gene=True)
