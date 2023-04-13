# -*- coding: utf-8 -*-
"""Untitled4.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dkNeQ52xlKm9wmrI5Hn1k7ehCckSECxQ
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import tensorflow_datasets as tfds
import matplotlib.pyplot as plt
import numpy as np

dataset, info = tfds.load('oxford_iiit_pet:3.*.*', with_info=True)

def resize(image, mask):
   image = tf.image.resize(image, (128, 128), method="nearest")
   mask = tf.image.resize(mask, (128, 128), method="nearest")
   return image, mask

def normalize(image, mask):
   image = tf.cast(image, tf.float32) / 255.0
   mask -= 1
   return image, mask

def trainImage(datapoint):
   image = datapoint["image"]
   mask = datapoint["segmentation_mask"]
   image, mask = resize(image, mask)
   image, mask = normalize(image, mask)

   return image, mask

def testImage(datapoint):
   image = datapoint["image"]
   mask = datapoint["segmentation_mask"]
   image, mask = resize(image, mask)
   image, mask = normalize(image, mask)

   return image, mask

train_dataset = dataset["train"].map(trainImage, num_parallel_calls=tf.data.AUTOTUNE)
test_dataset = dataset["test"].map(testImage, num_parallel_calls=tf.data.AUTOTUNE)

batchSize = 64
bufferSize = 1000
trainBatches = train_dataset.cache().shuffle(bufferSize).batch(batchSize).repeat()
trainBatches = trainBatches.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)
validationBatches = test_dataset.take(3000).batch(batchSize)
testBatches = test_dataset.skip(3000).take(669).batch(batchSize)

epochNumber = 20
lengthOfTrain = info.splits["train"].num_examples
stepsPerEpoch = lengthOfTrain // batchSize
valSubNumber = 5
lengthOfTest = info.splits["test"].num_examples
validationSteps = lengthOfTest // batchSize // valSubNumber

import keras.backend as K

def dice_coef(y_true, y_pred, smooth=1):
    y_true = K.one_hot(K.cast(y_true, 'int32'), num_classes=3)
    y_pred = K.one_hot(K.argmax(y_pred), num_classes=3)
    y_true_f = K.flatten(y_true)
    y_pred_f = K.flatten(y_pred)
    intersection = K.sum(y_true_f * y_pred_f)
    return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_loss(y_true, y_pred):
    return 1 - dice_coef(y_true, y_pred)

def linkNet256():

  from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, Add
  from keras.models import Model
  import tensorflow as tf

  # Input Layer
  inputs = Input(shape=(128, 128, 3))

  # Encoder Layers
  e1 = Conv2D(64, 3, activation='relu', padding='same')(inputs)
  EN1 = MaxPooling2D(pool_size=(2, 2))(e1)

  e2 = Conv2D(128, 3, activation='relu', padding='same')(EN1)
  EN2 = MaxPooling2D(pool_size=(2, 2))(e2)

  e3 = Conv2D(256, 3, activation='relu', padding='same')(EN2)
  EN3 = MaxPooling2D(pool_size=(2, 2))(e3)

  # Decoder Layers
  
  d3 = UpSampling2D(size=(2, 2))(EN3)
  DC3 = Conv2D(256, 3, activation='relu', padding='same')(d3)

  result2 = tf.keras.layers.concatenate([EN2, DC3])

  d2 = UpSampling2D(size=(2, 2))(result2)
  DC2 = Conv2D(128, 3, activation='relu', padding='same')(d2)

  result3 = tf.keras.layers.concatenate([EN1, DC2])

  d1 = UpSampling2D(size=(2, 2))(result3)
  DC1 = Conv2D(64, 3, activation='relu', padding='same')(d1)

  # Output layer
  output = Conv2D(3, 3, activation='softmax', padding='same')(DC1)

  model = Model(inputs=inputs, outputs=output)

  model.compile(optimizer='SGD', loss='sparse_categorical_crossentropy', metrics=['accuracy',dice_coef])

  model.summary()
  with tf.device('/device:GPU:0'):
    history = model.fit(trainBatches, epochs=epochNumber, steps_per_epoch=stepsPerEpoch, validation_steps=validationSteps,validation_data=testBatches)

  return model

def linkNet512():

  from keras.layers import Input, Conv2D, MaxPooling2D, UpSampling2D, Add
  from keras.models import Model
  import tensorflow as tf

  # Input Layer
  inputs = Input(shape=(128, 128, 3))

  # Encoder Layers
  e1 = Conv2D(64, 3, activation='relu', padding='same')(inputs)
  EN1 = MaxPooling2D(pool_size=(2, 2))(e1)

  e2 = Conv2D(128, 3, activation='relu', padding='same')(EN1)
  EN2 = MaxPooling2D(pool_size=(2, 2))(e2)

  e3 = Conv2D(256, 3, activation='relu', padding='same')(EN2)
  EN3 = MaxPooling2D(pool_size=(2, 2))(e3)

  e4 = Conv2D(512, 3, activation='relu', padding='same')(EN3)
  EN4 = MaxPooling2D(pool_size=(2, 2))(e4)


  # Decoder Layers
  d4 = UpSampling2D(size=(2, 2))(EN4)
  DC4 = Conv2D(512, 3, activation='relu', padding='same')(d4)

  result1 = tf.keras.layers.concatenate([EN3, DC4])

  d3 = UpSampling2D(size=(2, 2))(result1)
  DC3 = Conv2D(256, 3, activation='relu', padding='same')(d3)

  result2 = tf.keras.layers.concatenate([EN2, DC3])

  d2 = UpSampling2D(size=(2, 2))(result2)
  DC2 = Conv2D(128, 3, activation='relu', padding='same')(d2)

  result3 = tf.keras.layers.concatenate([EN1, DC2])

  d1 = UpSampling2D(size=(2, 2))(result3)
  DC1 = Conv2D(64, 3, activation='relu', padding='same')(d1)

  # Output layer
  output = Conv2D(3, 3, activation='softmax', padding='same')(DC1)


  # Create the model
  model = Model(inputs=inputs, outputs=output)

  model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy',dice_coef])

  model.summary()
  with tf.device('/device:GPU:0'):
    history = model.fit(trainBatches, epochs=epochNumber, steps_per_epoch=stepsPerEpoch, validation_steps=validationSteps,validation_data=testBatches)

  return model

model = linkNet512()
model.save('linkNet512.h5')

import matplotlib.pyplot as plt

from keras.saving.save import load_model

#model = load_model('/content/linkNet512.h5')

history = model.history

dice_coef = history.history['dice_coef']
val_dice_coef = history.history['val_dice_coef']
accuracy = history.history['accuracy']
val_accuracy = history.history['val_accuracy']


plt.plot(dice_coef)
plt.plot(val_dice_coef)
plt.title('Dice coefficient')
plt.ylabel('Dice coefficient')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()

plt.plot(accuracy)
plt.plot(val_accuracy)
plt.title('Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Validation'], loc='upper left')
plt.show()