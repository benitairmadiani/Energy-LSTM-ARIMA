# -*- coding: utf-8 -*-
"""05211840000063_FPTEKPER.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-rSeRfbnwtf-drX61UcOin7s-5j_saTv

Dataset Source: https://www.kaggle.com/nicholasjhana/energy-consumption-generation-prices-and-weather
"""

# Commented out IPython magic to ensure Python compatibility.
import numpy as np 
import pandas as pd

import matplotlib.pyplot as plt
import pandas as pd
pd.set_option('display.float_format', lambda x: '%.4f' % x)
import seaborn as sns
sns.set_context("paper", font_scale=1.3)
sns.set_style('white')
import warnings
warnings.filterwarnings('ignore')
from time import time
import matplotlib.ticker as tkr
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from sklearn import preprocessing
from statsmodels.tsa.stattools import pacf
# %matplotlib inline
import math
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Dropout
from keras.layers import *
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from keras.callbacks import EarlyStopping

"""# Load Data"""

from google.colab import drive
drive.mount("/content/gdrive")

df = pd.read_csv('/content/gdrive/My Drive/energy_dataset.csv')

df.head()

df.info()

xpoint = df['time'].iloc[0:200]
ypoint = df['total load actual'].iloc[0:200]
plt.plot(xpoint,ypoint)
plt.show()

mape = np.mean(np.abs((df['total load actual'] - df['total load forecast']) / df['total load actual'])) * 100
print('MAPE of the forecasted data present in DataFrame:', mape)

"""# Preprocess Data"""

data = df.copy()

data = data.filter(['time','total load actual'])
data.head()

data.isnull().sum()

data = data.dropna()

data.isnull().sum()

data['time'] = pd.to_datetime(data['time'], utc=True)
data['time'] = data['time'].dt.tz_localize(None)
data.head()

data = data.set_index(pd.DatetimeIndex(data['time']))
data.drop('time', axis=1, inplace=True)
data.head()

from statsmodels.tsa.seasonal import seasonal_decompose

result = seasonal_decompose(data, model='multiplicative', freq=24)
result.plot()
plt.show()

"""Diketahui bahwa dataset adalah seasonal dan tidak memiliki trend."""

dataset = data.astype('float32') 
dataset = np.reshape(dataset, (-1, 1)) # reshape to one feature; required for the models

scaler = MinMaxScaler(feature_range=(0, 1)) # Min Max scaler
dataset = scaler.fit_transform(dataset) # fit and transform the dataset

# Train and Test splits
train_size = int(len(dataset) * 0.80) 
test_size = len(dataset) - train_size
train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]

def create_dataset(dataset, look_back=1):
    X, Y = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), 0]
        X.append(a)
        Y.append(dataset[i + look_back, 0])
    return np.array(X), np.array(Y)

look_back = 25 # timesteps to lookback for predictions
X_train, trainY = create_dataset(train, look_back)
X_test, testY = create_dataset(test, look_back)

# reshape input to be [samples, time steps, features]
X_train = np.reshape(X_train, (X_train.shape[0], 1, X_train.shape[1]))
X_test = np.reshape(X_test, (X_test.shape[0], 1, X_test.shape[1]))
print("Shapes: \nTraining set: {}, Testing set: {}".format(X_train.shape, X_test.shape))
print("Sample from training set: \n{}".format(X_train[0]))

"""# Build Model

## Auto Regressive
"""

from statsmodels.tsa.ar_model import AR

model_AR = AR(train)
model_AR_fit = model_AR.fit()

test_predict_AR = model_AR_fit.predict(start=len(train), end=len(train)+len(test)-1, dynamic=False)
# invert predictions
test_predict_AR = scaler.inverse_transform(test_predict_AR.reshape(-1, 1))
Y_test_AR = scaler.inverse_transform(test)
print('Test Mean Absolute Error:', mean_absolute_error(Y_test_AR, test_predict_AR))
print('Test Root Mean Squared Error:',np.sqrt(mean_squared_error(Y_test_AR, test_predict_AR)))

from sklearn.metrics import mean_absolute_percentage_error

mape_AR = mean_absolute_percentage_error(Y_test_AR, test_predict_AR)
print("Testing MAPE: {}".format(mape_AR))

idx = 200
aa=[x for x in range(idx)]
plt.figure(figsize=(8,4))
plt.plot(aa, Y_test_AR[:idx], marker='.', label="actual")
plt.plot(aa, test_predict_AR[:idx], 'r', label="prediction")
# plt.tick_params(left=False, labelleft=True) #remove ticks
plt.tight_layout()
sns.despine(top=True)
plt.subplots_adjust(left=0.07)
plt.ylabel('TOTAL Load', size=15)
plt.xlabel('Time step', size=15)
plt.legend(fontsize=15)
plt.show();

"""## Moving Average"""

# Moving Average 25 periods
test_predict_MA = np.mean(X_test, axis=2)
print('Test Mean Absolute Error:', mean_absolute_error(testY, test_predict_MA))
print('Test Root Mean Squared Error:',np.sqrt(mean_squared_error(testY, test_predict_MA)))

from sklearn.metrics import mean_absolute_percentage_error

mape_MA = mean_absolute_percentage_error(testY, test_predict_MA)
print("Testing MAPE: {}".format(mape_MA))

idx = 200
aa=[x for x in range(idx)]
plt.figure(figsize=(8,4))
plt.plot(aa, testY[:idx], marker='.', label="actual")
plt.plot(aa, test_predict_MA[:idx], 'r', label="prediction")
# plt.tick_params(left=False, labelleft=True) #remove ticks
plt.tight_layout()
sns.despine(top=True)
plt.subplots_adjust(left=0.07)
plt.ylabel('TOTAL Load', size=15)
plt.xlabel('Time step', size=15)
plt.legend(fontsize=15)
plt.show();

"""## LSTM"""

dataset = data.astype('float32')
dataset = np.reshape(dataset, (-1, 1))
scaler = MinMaxScaler(feature_range=(0, 1))
dataset = scaler.fit_transform(dataset)
train_size = int(len(dataset) * 0.80)
test_size = len(dataset) - train_size
train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]

def create_dataset(dataset, look_back=1):
    X, Y = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), 0]
        X.append(a)
        Y.append(dataset[i + look_back, 0])
    return np.array(X), np.array(Y)

look_back = 25
X_train, Y_train = create_dataset(train, look_back)
X_test, Y_test = create_dataset(test, look_back)

X_train = np.reshape(X_train, (X_train.shape[0], 1, X_train.shape[1]))
X_test = np.reshape(X_test, (X_test.shape[0], 1, X_test.shape[1]))

model_LSTM = Sequential()
model_LSTM.add(LSTM(100, input_shape=(X_train.shape[1], X_train.shape[2])))
model_LSTM.add(Dropout(0.2))
model_LSTM.add(Dense(1))
model_LSTM.compile(loss='mean_absolute_percentage_error', optimizer='adam')

history = model_LSTM.fit(X_train, Y_train, epochs=100, batch_size=16, validation_data=(X_test, Y_test),verbose=1, shuffle=False)

model_LSTM.summary()

train_predict_LSTM = model_LSTM.predict(X_train)
test_predict_LSTM = model_LSTM.predict(X_test)
# invert predictions
train_predict_LSTM = scaler.inverse_transform(train_predict_LSTM)
Y_train = scaler.inverse_transform([Y_train])
test_predict_LSTM = scaler.inverse_transform(test_predict_LSTM)
Y_test = scaler.inverse_transform([Y_test])
print('Train Mean Absolute Error:', mean_absolute_error(Y_train[0], train_predict_LSTM[:,0]))
print('Train Root Mean Squared Error:',np.sqrt(mean_squared_error(Y_train[0], train_predict_LSTM[:,0])))
print('Test Mean Absolute Error:', mean_absolute_error(Y_test[0], test_predict_LSTM[:,0]))
print('Test Root Mean Squared Error:',np.sqrt(mean_squared_error(Y_test[0], test_predict_LSTM[:,0])))

mape_train_LSTM = np.mean(np.abs((Y_train[0] - train_predict_LSTM[:,0]) / Y_train[0])) * 100
mape_test_LSTM = np.mean(np.abs((Y_test[0] - test_predict_LSTM[:,0]) / Y_test[0])) * 100

print("Train MAPE: {}, Test MAPE: {}".format(mape_train_LSTM, mape_test_LSTM))

from sklearn.metrics import mean_absolute_percentage_error

mape_train_LSTM = mean_absolute_percentage_error(Y_train, train_predict_LSTM)
mape_test_LSTM = mean_absolute_percentage_error(Y_test, test_predict_LSTM)
print("Train MAPE: {}, Test MAPE: {}".format(mape_train_LSTM, mape_test_LSTM))

plt.figure(figsize=(8,4))
plt.plot(history.history['loss'], label='Train Loss')
plt.plot(history.history['val_loss'], label='Test Loss')
plt.title('model loss')
plt.ylabel('loss')
plt.xlabel('epochs')
plt.legend(loc='upper right')
plt.show();

idx = 200
aa=[x for x in range(idx)]
plt.figure(figsize=(8,4))
plt.plot(aa, Y_test[0][:idx], marker='.', label="actual")
plt.plot(aa, test_predict_LSTM[:,0][:idx], 'r', label="prediction")
# plt.tick_params(left=False, labelleft=True) #remove ticks
plt.tight_layout()
sns.despine(top=True)
plt.subplots_adjust(left=0.07)
plt.ylabel('TOTAL Load', size=15)
plt.xlabel('Time step', size=15)
plt.legend(fontsize=15)
plt.show();

"""## ARIMA"""

! pip install pmdarima
from pmdarima.arima import auto_arima

model_ARIMA =  auto_arima(train,start_p=1, d=1, start_q=0, 
                          max_p=5, max_d=5, max_q=5, start_P=0, 
                          D=1, start_Q=0, max_P=5, max_D=5,
                          max_Q=5, m=24, seasonal=True, 
                          error_action='warn',trace = True,
                          supress_warnings=True,stepwise = True, maxiter=20)
model_ARIMA_fit = model_ARIMA.fit(disp=False)

test_predict_ARIMA = model_ARIMA_fit.predict(start=len(train), end=len(train)+len(test)-1, dynamic=False)
# invert predictions
test_predict_ARIMA = scaler.inverse_transform(test_predict.reshape(-1, 1))
Y_test_ARIMA = scaler.inverse_transform(test)
print('Test Mean Absolute Error:', mean_absolute_error(Y_test_ARIMA, test_predict_ARIMA))
print('Test Root Mean Squared Error:',np.sqrt(mean_squared_error(Y_test_ARIMA, test_predict_ARIMA)))

from sklearn.metrics import mean_absolute_percentage_error

mape_ARIMA = mean_absolute_percentage_error(Y_test_ARIMA, test_predict_ARIMA)
print("Testing MAPE: {}".format(mape_ARIMA))

idx = 200
aa=[x for x in range(idx)]
plt.figure(figsize=(8,4))
plt.plot(aa, Y_test_ARIMA[:idx], marker='.', label="actual")
plt.plot(aa, test_predict_ARIMA[:idx], 'r', label="prediction")
# plt.tick_params(left=False, labelleft=True) #remove ticks
plt.tight_layout()
sns.despine(top=True)
plt.subplots_adjust(left=0.07)
plt.ylabel('TOTAL Load', size=15)
plt.xlabel('Time step', size=15)
plt.legend(fontsize=15)
plt.show();