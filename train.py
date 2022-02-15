# data_train.py
import re
import os
import json
import numpy as np
import pandas as pd
import pickle
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import LogisticRegression
from sklearn.linear_model import Lasso
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
#import TabularAutoEncoder
import VAE
#import tensorflow.compat.v1 as tf
#tf.disable_v2_behavior()
import tensorflow as tf
import torch
from torch import nn
import torchvision
from torch.autograd import Variable
#import AutoEncoder
import math
import warnings
import AutoEncoder as AE
from time import time

warnings.filterwarnings("ignore")


def origin_data(data):
    return data


def square_data(data):
    return data ** 2


def log_data(data):
    return np.log(data + 1e-5)


def radical_data(data):
    return data ** (1 / 2)


def cube_data(data):
    return data ** 3


# Only train regression model, save parameters to pickle file
def run(code, X_train, y_train, platform, model_type, data_type):
    data_dict = {'origin_data': origin_data, 'square_data': square_data, 'log_data': log_data,
                 'radical_data': radical_data, 'cube_data': cube_data}
    model_dict = {'LinearRegression': LinearRegression, 'LogisticRegression': LogisticRegression,
                  'L1': Lasso, 'L2': Ridge, 'RandomForest': RandomForestRegressor,'VAE':VAE.VAE,'AE':AE.Autoencoder}

    with open(platform, 'r') as f:
        gene_dict = json.load(f)
        f.close()

    count = 0
    num = len(gene_dict)
    gene_list = []
    print('Now start training gene...')

    data_train = data_dict[data_type](X_train)

    gene_data_train = []
    residuals_name = []

    for (i,gene) in enumerate(gene_dict):
        count += 1
        #gene_data_train = []
        #residuals_name = []
        for residue in data_train.index:
            if residue in gene_dict[gene]:
                gene_data_train.append(data_train.loc[residue])
                residuals_name.append(residue)
        if len(gene_data_train) == 0:
            # print('Contained Nan data, has been removed!')
            continue

        #gene_data_train = np.array(gene_data_train)
        gene_list.append(gene)
        print('Now training ' + gene + "\tusing " + model_type + "\ton " + data_type + "\t" + str(
            int(count * 100 / num)) + '% ...')
        print("gene_data_train.shape[1]")
        print(np.array(gene_data_train).shape[1])


        print('finish!')
    gene_data_train = np.array(gene_data_train)#added line on 2-3
    print("gene_data_train=")
    print(gene_data_train)
    if (model_type == "VAE" or model_type == "AE"):
        num_epochs = 50
        batch_size = 100
        hidden_size = 10
        dataset = gene_data_train  # dsets.MNIST(root='../data',
        # train=True,
        # transform=transforms.ToTensor(),
        # download=True)
        data_loader = torch.utils.data.DataLoader(dataset=dataset,
                                                  batch_size=batch_size,
                                                  shuffle=True)
        print("gene_data_train.shape")
        print(gene_data_train.shape)
        ae = AE.Autoencoder(in_dim=gene_data_train.shape[1], h_dim=hidden_size)
        if torch.cuda.is_available():
            ae.cuda()

        criterion = nn.BCELoss()
        optimizer = torch.optim.Adam(ae.parameters(), lr=0.001)
        iter_per_epoch = len(data_loader)
        data_iter = iter(data_loader)

        # save fixed inputs for debugging
        fixed_x = next(data_iter)  # fixed_x, _ = next(data_iter)
        mydir = 'E:/JI/4 SENIOR/2021 fall/VE490/ReGear-gyl/ReGear/test_sample/data/'
        myfile = 'real_image_%s_%d.png' % (code, i)
        images_path = os.path.join(mydir, myfile)
        torchvision.utils.save_image(Variable(fixed_x).data.cpu(), images_path)
        fixed_x = AE.to_var(fixed_x.view(fixed_x.size(0), -1))

        for epoch in range(num_epochs):
            t0 = time()
            for i, (images) in enumerate(data_loader):  # for i, (images, _) in enumerate(data_loader):

                # flatten the image
                images = AE.to_var(images.view(images.size(0), -1))
                images = images.float()
                out = ae(images)
                loss = criterion(out, images)

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

                if (i + 1) % 100 == 0:
                    print('Epoch [%d/%d], Iter [%d/%d] Loss: %.4f Time: %.2fs'
                          % (epoch + 1, num_epochs, i + 1, len(dataset) // batch_size, loss.item(),
                             time() - t0))  # original version: loss.item() was loss.data[0]

            if (epoch + 1) % 10 == 0:
                # save the reconstructed images
                fixed_x = fixed_x.float()
                reconst_images = ae(fixed_x)
                reconst_images = reconst_images.view(reconst_images.size(0), gene_data_train.shape[
                    1])  # reconst_images = reconst_images.view(reconst_images.size(0), 1, 28, 28)
                mydir = 'E:/JI/4 SENIOR/2021 fall/VE490/ReGear-gyl/ReGear/test_sample/data/'
                myfile = 'reconst_images_%s_%d_epoch%d.png' % (code, i, (epoch + 1))
                reconst_images_path = os.path.join(mydir, myfile)
                torchvision.utils.save_image(reconst_images.data.cpu(), reconst_images_path)
            ##################
            model = model_dict[model_type]()

        if count == 1:
            with open(code + "_" + model_type + "_" + data_type + 'train_model.pickle', 'wb') as f:
                pickle.dump((gene, ae), f)  # pickle.dump((gene, model), f)
        else:
            with open(code + "_" + model_type + "_" + data_type + 'train_model.pickle', 'ab') as f:
                pickle.dump((gene, ae), f)  # pickle.dump((gene, model), f)
    else:
        model = model_dict[model_type]()
        model.fit(gene_data_train.T, y_train)
        if model_type == "RandomForest":
            print("The number of residuals involved in the gene {} is {}".format(gene, len(gene_data_train)))
            print("The feature importance is ")
            print(model.feature_importances_)
            print("The names of residuals are ")
            print(residuals_name)
            print(15 * '-')

        if count == 1:
            with open(code + "_" + model_type + "_" + data_type + 'train_model.pickle', 'wb') as f:
                pickle.dump((gene, model), f)
        else:
            with open(code + "_" + model_type + "_" + data_type + 'train_model.pickle', 'ab') as f:
                pickle.dump((gene, model), f)
    print("Training finish!")


def train_VAE(model,train_db,optimizer=tf.keras.optimizers.Adam(0.001),n_input=80):
    for epoch in range(1000):
        for step, x in enumerate(train_db):
            x = tf.reshape(x, [-1, n_input])
            with tf.GradientTape() as tape:
                x_rec_logits, mean, log_var = model(x)
                rec_loss = tf.losses.binary_crossentropy(x, x_rec_logits, from_logits=True)
                rec_loss = tf.reduce_mean(rec_loss)
                # compute kl divergence (mean, val) ~ N(0, 1)
                kl_div = -0.5 * (log_var + 1 - mean ** 2 - tf.exp(log_var))
                kl_div = tf.reduce_mean(kl_div) / x.shape[0]
                # loss
                loss = rec_loss + 1.0 * kl_div

            grads = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))

            if step % 10 == 0:
                print(epoch, step, 'kl_div:', float(kl_div), 'rec_loss:', rec_loss)


if __name__ == '__main__':
    # Parameter description：
    # code: dataSet ID such as GSE66695 ( string )
    # train_file: train data filename( .txt )
    # label_file: train label filename(.txt)
    # platform: Gene correspond to methylation characteristics( json file )
    # model_type: type of regression model ( string )
    # data_type: type of data ( string )

    # example

    code = "GSE66695"
    train_file = "data_train.txt"
    label_file = "label_train.txt"
    platform = "platform.json"
    model_type = "LinearRegression"
    data_type = "origin_data"

    train_data = pd.read_table(train_file, index_col=0)
    train_label = pd.read_table(label_file, index_col=0).values.ravel()

    run(code, train_data, train_label, platform, model_type, data_type)
