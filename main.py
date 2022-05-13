#-*- coding : utf-8-*-
# coding:unicode_escape
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

from train_keras_redefined_loss import run
from predict_keras_redefined_loss import predict
#from test import select_feature
import torch
torch.set_printoptions(profile="full")
#from torchsummary import summary
code = "diabetes1"#"GSE66695"#GSE42861_processed_methylation_matrix #"GSE66695-series"
platform = "platform.json"
model_type = "AE"#"RandomForest"
predict_model_type="L2"
data_type = "origin_data"
dataset_type="train"
isTrain=True
toTrainAE=True
toTrainNN=True
isPredict=True
toTrainMeiNN=True
toAddGeneSite=True
num_of_selected_residue=5000
model=None
AE_epoch=1000
NN_epoch=1000
ae=None
fcn=None
myMeiNN=None
h_dim=30

date = '5-13-kerasAE-reg-myloss-explainable-h_dim%d-epoch%d-geneSite=%s-selected%d'%(h_dim,AE_epoch,toAddGeneSite,num_of_selected_residue)
keras = True
path = r"./result/"


filename_dict={'small':"./dataset/data_train.txt"}




def data_preprocessing(data_train):

    y_train = data_train.iloc[:, -1].T
    data_train= data_train.iloc[:, :-1].T

    data_train_df = pd.DataFrame(data_train)
    print("data_train_df=")
    print(data_train_df)
    print("y_train")
    print(y_train)
    if code == "GSE66695":
        data_label_df0 = pd.DataFrame(y_train, columns=['Ground Truth'], index=data_train_df.columns)
    else:
        data_label_df0 = pd.DataFrame(y_train, columns=['Ground Truth'])
    data_label_df = data_label_df0.T
    print("data_label_df=")
    print(data_label_df)
    data_train_label_df = data_train_df.append(data_label_df)  # pd.concat([data_train_df, data_label_df], axis=0)
    print("after join data and label")
    print(data_train_label_df)
    from scipy import stats
    data_train_label_df_T = data_train_label_df.T
    print("data_train_label_df_T[data_train_label_df_T['Ground Truth']==1.0]")
    print(data_train_label_df_T[data_train_label_df_T['Ground Truth'] == 1.0])
    t_test_result = stats.ttest_ind(data_train_label_df_T[data_train_label_df_T['Ground Truth'] == 1.0],
                                    data_train_label_df_T[data_train_label_df_T['Ground Truth'] == 0.0])
    print("t_testresult=")
    print(t_test_result)
    print("t_testresult.pvalue=")
    print(t_test_result.pvalue)
    print("t_testresult.pvalue.shape=")
    print(t_test_result.pvalue.shape)

    data_train_label_df['pvalue'] = t_test_result.pvalue
    print("data_train_label_df added pvalue")
    print(data_train_label_df)
    print("t_testresult.pvalue.sort()=")
    print(np.sort(t_test_result.pvalue))
    print("data_train_label_df.sort_values(by='pvalue',ascending=True)")
    data_train_label_df_sorted_by_pvalue = data_train_label_df.sort_values(by='pvalue', ascending=True)
    print(data_train_label_df_sorted_by_pvalue)
    print("data_train_label_df_sorted_by_pvalue.iloc[1:,:-1])")
    data_train_label_df_sorted_by_pvalue_raw = data_train_label_df_sorted_by_pvalue.iloc[:, :-1]#[1:, :-1]
    print(data_train_label_df_sorted_by_pvalue_raw)

    selected_residue_train_data = data_train_label_df_sorted_by_pvalue_raw.iloc[:num_of_selected_residue+1, :]
    print("selected_residue_train_data)")
    print(selected_residue_train_data)
    data_train = selected_residue_train_data

    return data_train



if not code == "GSE66695":
    isSelfCollectedDataset = True
    train_dataset_filename=r"./dataset/"+code+"/beta_value.csv"#"./dataset/data_train.txt"#"./dataset/diabetes1/beta_value.csv"#"./dataset/data_train.txt"# GSE66695_series_matrix.txt"#r"./dataset/data_train.txt"#GSE42861_processed_methylation_matrix.txt
    train_label_filename= r"./dataset/"+code+"/label.csv"#"./dataset/label_train.txt"#"./dataset/diabetes1/label.csv"#"./dataset/label_train.txt"
    test_dataset_filename= r"./dataset/"+code+"/beta_value.csv"#"./dataset/data_test.txt"#"./dataset/diabetes1/beta_value.csv"#"./dataset/data_test.txt"
    test_label_filename= r"./dataset/"+code+"/label.csv"#"./dataset/label_test.txt"#"./dataset/diabetes1/label.csv"#"./dataset/label_test.txt"
else:
    isSelfCollectedDataset = False
    train_dataset_filename = r"./dataset/data_train.txt"#"./dataset/diabetes1/beta_value.csv"#"./dataset/data_train.txt"# GSE66695_series_matrix.txt"#r"./dataset/data_train.txt"#GSE42861_processed_methylation_matrix.txt
    train_label_filename = r"./dataset/label_train.txt"#"./dataset/diabetes1/label.csv"#"./dataset/label_train.txt"
    test_dataset_filename = r"./dataset/data_test.txt"#"./dataset/diabetes1/beta_value.csv"#"./dataset/data_test.txt"
    test_label_filename = r"./dataset/label_test.txt" #
just_check_data=False
toAddGenePathway=False
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

# train
if True or isTrain:
    #train_data = pd.read_excel(train_dataset_filename,skiprows=30)#, index_col=0,names=['0','1']#,delimiter='!|\t'
    #train_data['0'].str.split('\t', expand=True)
    if isSelfCollectedDataset:
        train_data_total = pd.read_csv(train_dataset_filename,index_col=0)#,skiprows=30,delimiter='\t')
        train_label_total_csv = pd.read_csv(train_label_filename, index_col=0)#.values.ravel()
        train_label_total_csv_df = pd.DataFrame(train_label_total_csv)
        train_data_and_label_df = pd.concat([train_data_total,train_label_total_csv_df.T],axis=0)

        train_data_and_label_df = data_preprocessing(train_data_and_label_df.T)
        train_data, test_data = train_test_split(train_data_and_label_df.T, train_size=0.75, random_state=10)

        train_label = train_data.iloc[:,-0].T#train_data.iloc[:,-1].T
        test_label=test_data.iloc[:,0].T#test_data.iloc[:,-1].T
        train_data = train_data.iloc[:, 1:].T#train_data.iloc[:, :-1].T
        test_data = test_data.iloc[:, 1:].T #test_data.iloc[:, :-1].T
        print("train_data_and_label_df")
        print(train_data_and_label_df)

        print("read train_data_total.shape:")
        print(train_data_total.shape)
        print(train_data_total)

        print("finish read train data")
        #train_data,test_data=train_test_split(train_data_total, train_size=0.75, random_state=10)
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
    else:
        train_data = pd.read_table(train_dataset_filename,index_col=0)
        print("read train_data.shape:")
        print(train_data.shape)
        print(train_data[0:15])
        train_data.head(10)
        print("finish read train data")
        train_label = pd.read_table(train_label_filename, index_col=0).values.ravel()
        print("finish read train label")
        print(train_data.head(10))
        test_data = pd.read_table(test_dataset_filename, index_col=0)
        test_label = pd.read_table(test_label_filename, index_col=0)

if isTrain:
    if(not just_check_data):
        if keras and toTrainMeiNN == True:
            myMeiNN,residue_name_list = run(path, date, code, train_data, train_label, platform, model_type, data_type, h_dim,
                          toTrainMeiNN=toTrainMeiNN, toAddGenePathway=toAddGenePathway,toAddGeneSite=toAddGeneSite,num_of_selected_residue=num_of_selected_residue,AE_epoch_from_main=AE_epoch,NN_epoch_from_main=NN_epoch)
            myMeiNN.fcn.summary()
            myMeiNN.autoencoder.summary()
        elif(toTrainMeiNN==False):
            (ae, fcn) = run(path, date, code, train_data, train_label, platform, model_type, data_type, h_dim,
                            toTrainAE, AE_epoch, NN_epoch)
            ae.summary()
            fcn.summary()
        else:
            run(path,date, code, train_data, train_label, platform, model_type, data_type, h_dim, toTrainAE,toTrainNN, AE_epoch, NN_epoch)
'''
if keras:
    ae.summary()
    fcn.summary()
'''
residue_name_list=np.load(path + date + "_" + code + "_gene_level" + "(" + data_type + '_' + model_type + "_original_residue_name_list)" + ".txt.npy")
# predict
if isPredict and (not just_check_data):
    #test_data = pd.read_table(test_dataset_filename, index_col=0)
    #test_label = pd.read_table(test_label_filename, index_col=0)
    predict(path,date,code, test_data, test_label,platform, date+"_"+code +"_"+model_type+"_"+data_type+dataset_type+"_model.pickle", model_type, data_type,model,predict_model_type,residue_name_list)



print("test label is")
print(test_label)

'''
# test(feature selection)
data = pd.read_table(r"./dataset/"+date+"_"+code+"_gene_level("+data_type+"_"+model_type+").txt", index_col=0)
label = pd.read_table(test_label_filename, index_col=0).values.ravel()
'''
#select_feature(code, data, label, gene=True)
