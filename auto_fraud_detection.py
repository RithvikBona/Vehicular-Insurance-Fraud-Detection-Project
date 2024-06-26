# -*- coding: utf-8 -*-
"""Auto_Fraud_Detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/13hgzCohs_zZlXNJEH58_Y4s3Id6tZXl8

# Auto-Fraud Detection

### This projects involves creating a data pipeline and ml model to take images of cars from insurance claim and classify the claims as fraudulent (1) or not (0).
"""

# Imports

import pandas as pd
from sklearn.metrics import recall_score
import numpy as np
import cv2
import random
import matplotlib.pyplot as plt
import os
from PIL import Image
from sklearn.metrics import recall_score, accuracy_score
from imblearn.under_sampling import EditedNearestNeighbours
from imblearn.under_sampling import RandomUnderSampler
from imblearn.over_sampling import RandomOverSampler
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from imblearn.combine import SMOTEENN

# Mount google drive and connect to csv
# drive.mount('/content/gdrive')

# Directory containing JPEG images
image_directory = '/Users/barivadaria/Developer/Code/AI4ALL Bootcamp/Machine Learning Insurance Fraud Project/Test Data/archive'
image_train_fraud_directory = image_directory + '/train/Fraud'
image_train_non_fraud_directory = image_directory + '/train/Non-Fraud'
image_test_fraud_directory = image_directory + '/test/Fraud'
image_test_non_fraud_directory = image_directory + '/test/Non-Fraud'


# Function to get images from directory and put them in list
# Input Parameters: directory
# Return list of images
# Get images in train_non_fraud directory
# Iterate over files in directory
def get_imgs(directory):
    img_list = []
    for file_name in os.listdir(directory)[:1750]:
        if file_name.endswith('.jpg'):
            # Get full path
            file_path = os.path.join(directory, file_name)
            # Read images
            img = Image.open(file_path)
            # Append image to image list
            img_list.append(img)
    return img_list


# Lists to store images
train_fraud_images = get_imgs(image_train_fraud_directory)
train_not_fraud_images = get_imgs(image_train_non_fraud_directory)
test_fraud_images = get_imgs(image_test_fraud_directory)
test_not_fraud_images = get_imgs(image_test_non_fraud_directory)

# Keep track of total width/height
total_width = 0
total_height = 0

# Iterate over all images totalling the width and height
for img in (test_fraud_images + train_fraud_images + test_not_fraud_images + train_not_fraud_images):
    total_height += img.height
    total_width += img.width

# Get mean height and width
mean_height = total_height / len(
    test_fraud_images + train_fraud_images + test_not_fraud_images + train_not_fraud_images)
mean_width = total_width / len(test_fraud_images + train_fraud_images + test_not_fraud_images + train_not_fraud_images)

# Round width and height to nearest 50
height = round(mean_height / 50) * 50
width = round(mean_width / 50) * 50

# Print results
print('Height: ', height)
print('Width: ', width)


# Function to get images from directory and put them in list
# Input Parameters: directory, height, width
# Return list of images
# Get images in train_non_fraud directory
# Iterate over files in directory
def resize_imgs(img_list, height, width):
    resize_tuple = (width, height)
    for img_counter in range(len(img_list)):
        img_list[img_counter] = img_list[img_counter].resize(resize_tuple)


# Lists to store resized images
resize_imgs(train_fraud_images, height, width)
resize_imgs(train_not_fraud_images, height, width)
resize_imgs(test_fraud_images, height, width)
resize_imgs(test_not_fraud_images, height, width)


def to_image_list(imgs):
    tensor_imgs = []

    for img in imgs:
        # Convert PIL Image to numpy array
        img_array = tf.keras.preprocessing.image.img_to_array(img)

        # Normalize pixel values
        img_array = img_array / 255.0

        tensor_imgs.append(img_array)

    return tensor_imgs


def to_ds(imgs, label):
    tensor_imgs = to_image_list(imgs)

    labels = [label] * len(imgs)
    img_dataset = tf.data.Dataset.from_tensor_slices((tensor_imgs, labels))

    return img_dataset


# Fraud = 1, Not Fraud = 0
# Convert image arrays to dataframes
train_fraud_ds = to_ds(train_fraud_images, 1).shuffle(buffer_size=7000)
train_not_fraud_ds = to_ds(train_not_fraud_images, 0).shuffle(buffer_size=7000)
test_fraud_ds = to_ds(test_fraud_images, 1).shuffle(buffer_size=7000)
test_not_fraud_ds = to_ds(test_not_fraud_images, 0).shuffle(buffer_size=7000)

# Get combined + randomized train and test dataframes
# Combine and shuffle the datasets
train_dataset = train_fraud_ds.concatenate(train_not_fraud_ds).shuffle(buffer_size=7000)
test_dataset = test_fraud_ds.concatenate(test_not_fraud_ds).shuffle(buffer_size=7000)

# Batch the datasets
batch_size = 64
train_dataset = train_dataset.batch(batch_size)
test_dataset = test_dataset.batch(batch_size)

# Visualize Class Proportions in Training
num_fraud = tf.data.experimental.cardinality(train_fraud_ds).numpy()
num_not_fraud = tf.data.experimental.cardinality(train_not_fraud_ds).numpy()
plt.pie(x=[num_fraud, num_not_fraud], labels=['Fraud', 'Not-Fraud'], autopct='%.2f%%')
plt.show()
# Inference - Major class imbalance with Not-Fraud as the majority and Fraud as the minority

"""### First iteration of ML"""

# Define the model
model = models.Sequential([
    layers.Conv2D(32, (3, 3), input_shape=(height, width, 3)),
    layers.MaxPooling2D((2, 2)),
    layers.Conv2D(64, (3, 3)),
    layers.MaxPooling2D((2, 2)),
    layers.Flatten(),
    layers.Dense(64, activation='relu'),
    layers.Dense(64, activation='relu'),
    layers.Dense(32, activation='relu'),
    layers.Dense(1, activation='sigmoid')
])

# Compile the model
model.compile(optimizer='adam',
              loss='binary_crossentropy',
              metrics=[tf.keras.metrics.Recall(), tf.keras.metrics.Accuracy()])

'''# Train the model
# model.fit(train_dataset, batch_size=batch_size, epochs=10, validation_data=test_dataset, verbose=1)'''


# Define a function to get predicted classes from probabilities based on a threshold
def get_predicted_classes(probabilities, threshold=0.5):
    return (probabilities > threshold).astype(int)


# Evaluate recall for base model
# Predict probabilities for base model


# Evaluate recall for each model
true_labels = []
model_predictions = []

# Assuming 'model' is your trained model and 'test_dataset' is properly batched
for images, labels in test_dataset:
    preds = model.predict(images)
    # Assuming a binary classification with a sigmoid activation at the output layer
    preds = (preds > 0.5).astype(int).flatten()

    model_predictions.extend(preds)
    true_labels.extend(labels.numpy())

# Convert lists to numpy arrays for metrics calculation
# true_labels = np.array(true_labels)
# model_predictions = np.array(model_predictions)

# Now, compute the recall
# recall = recall_score(true_labels, model_predictions)
# print(f'Base Recall: {recall}')

# accuracy = accuracy_score(true_labels, model_predictions)
# print(f"Base Accuracy: {accuracy}")

# test_probabilities = model.predict(test_dataset)

# Get predicted classes for each model using a threshold of 0.5
# test_predictions = get_predicted_classes(test_probabilities)

"""#### Data Alteration to Rectify Imbalanced Data

#### Functions
"""


'''# SMOTE ENN
def flat_array_images(img_list):
    flat_imgs = []
    for img in img_list:
        flat_imgs.append(np.array(img).flatten())
    return np.array(flat_imgs)


def create_tf_datasets(x_data, y_data, batch_size):
    dataset = tf.data.Dataset.from_tensor_slices((x_data, y_data))
    return dataset.shuffle(buffer_size=7000).batch(batch_size)


def prepare_balanced_dataset(train_fraud_images, train_not_fraud_images, height, width, batch_size=32):
    x_fraud_imgs = flat_array_images(train_fraud_images)
    x_not_fraud_imgs = flat_array_images(train_not_fraud_images)

    x = np.concatenate((x_fraud_imgs, x_not_fraud_imgs))
    y = np.array([1] * len(x_fraud_imgs) + [0] * len(x_not_fraud_imgs))

    smote_enn = SMOTEENN(random_state=0, sampling_strategy={0: 300, 1: 115})
    x_resampled, y_resampled = smote_enn.fit_resample(x, y)

    x_resampled_imgs = x_resampled.reshape((-1, height, width, 3))

    balanced_dataset = create_tf_datasets(x_resampled_imgs, y_resampled, batch_size)

    return balanced_dataset
'''

# Train Smote Dataset
'''smote_enn_train_dataset = prepare_balanced_dataset(train_fraud_images, train_not_fraud_images, height, width,
                                                   batch_size=32)'''


# Random Under Sampling
def randomly_undersample(non_fraud_images, ratio):
    new_data = []
    for img in non_fraud_images:
        if random.random() <= ratio:
            new_data.append(img)
    return new_data


# Random Over Sampling
def randomly_oversample(fraud_imgs, ratio):
    new_data = [img for img in fraud_imgs]
    for img in fraud_imgs:
        if random.random() <= ratio:
            new_data.append(img)

    return new_data


# Random Sampling Testing
undersampled_non_fraud = randomly_undersample(train_not_fraud_images, 0.75)
oversampled_fraud = randomly_oversample(train_fraud_images, 0.5)
undersampled_non_fraud_ds = to_ds(undersampled_non_fraud, 0)
oversampled_fraud_ds = to_ds(oversampled_fraud, 1)
# Randomly resampled train dataset
'''randomly_resampled_train_ds = oversampled_fraud_ds.concatenate(undersampled_non_fraud_ds).shuffle(
    buffer_size=7000).batch(batch_size)'''


# Data Augmentation
# Provide ranges for different kernels/augmentation methods.
def augment_data(my_dataset, proportion):
    datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.1,
        height_shift_range=0.1,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode='nearest')

    # Calculate the number of elements in the dataset
    num_elements = tf.data.experimental.cardinality(my_dataset).numpy()

    # Shuffle and take a proportion of the dataset to augment
    sampled_dataset = my_dataset.shuffle(1024).take(int(num_elements * proportion))

    def augment_image(x, y):
        # Wrap the augmentation inside tf.numpy_function
        # Adjusted to correctly handle the output
        x_aug = tf.numpy_function(
            func=lambda img: datagen.random_transform(img),
            inp=[x],
            Tout=tf.float32  # Ensure the output type matches your dataset
        )
        # Ensure x_aug has the correct shape after augmentation
        x_aug.set_shape(x.get_shape())
        return x_aug, y

    # Map the augment_image function over the sampled dataset
    augmented_dataset = sampled_dataset.map(augment_image)
    return my_dataset.concatenate(augmented_dataset)


'''# Augmented train dataset
augmented_train_fraud_ds = augment_data(train_fraud_ds, .5)
augmented_train_ds = augmented_train_fraud_ds.concatenate(train_not_fraud_ds).shuffle(buffer_size=7000).batch(
    batch_size)'''

# Data augmentation & randomly resampled dataset
augmented_resampled_train_fraud_ds = augment_data(oversampled_fraud_ds, .5)
augmented_resampled_train_ds = augmented_resampled_train_fraud_ds.concatenate(undersampled_non_fraud_ds).shuffle(
    buffer_size=7000).batch(batch_size)

"""### Training on Preprocessed Datasets"""


def evaluate_model(model, dataset):
    true_labels = []
    predictions = []

    # Iterate through the dataset to get batches of images and labels
    for images, labels in dataset:
        # Predict the probabilities for each image in the batch
        probs = model.predict(images)

        # Convert probabilities to binary predictions based on 0.5 threshold
        # This assumes your model outputs probabilities of the positive class (class 1)
        preds = (probs > 0.5).astype(int).flatten()

        # Extend the predictions and true_labels lists with the results
        predictions.extend(preds)
        true_labels.extend(labels.numpy().flatten())

    # Calculate recall and accuracy using true_labels and predictions
    recall = recall_score(true_labels, predictions)
    accuracy = accuracy_score(true_labels, predictions)

    return recall, accuracy

'''
# Train the model with weights to favor correctly predicting fraud (Heavy)
model.fit(train_dataset, batch_size=batch_size, epochs=10, validation_data=test_dataset, class_weight={0: .1, 1: 0.9})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Weighted Model Heavy - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the model with weights to favor correctly predicting fraud (Medium)
model.fit(train_dataset, batch_size=batch_size, epochs=10, validation_data=test_dataset, class_weight={0: .2, 1: 0.8})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Weighted Model Medium - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the model with weights to favor correctly predicting fraud (Light)
model.fit(train_dataset, batch_size=batch_size, epochs=10, validation_data=test_dataset, class_weight={0: .15, 1: 0.55})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Weighted Model Light - Recall: {recall}, Accuracy: {accuracy}") '''

'''# Train the data augmentation model
model.fit(augmented_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset)
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Augmented Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the randomly resampled model
model.fit(randomly_resampled_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset)
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Random Resample Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the SMOTE-ENN model
model.fit(smote_enn_train_dataset, batch_size=batch_size, epochs=10, validation_data=test_dataset)
recall, accuracy = evaluate_model(model, test_dataset)
print(f"SMOTE-ENN Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the data augmentation & randomly resampled model
model.fit(augmented_resampled_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset)
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Augmented & Resampled Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the heavy weighted & randomly resampled model
model.fit(randomly_resampled_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset,
          class_weight={0: 0.1, 1: 0.9})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Resamples & Heavy Weighted Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the light weighted & randomly resampled model
model.fit(randomly_resampled_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset,
          class_weight={0: 0.2, 1: 0.8})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Resamples & Light Weighted Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the data augmentation & heavy weighted model
model.fit(augmented_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset,
          class_weight={0: 0.1, 1: 0.9})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Augmented & Weighted Heavy Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the data augmentation & light weighted model
model.fit(augmented_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset,
          class_weight={0: 0.2, 1: 0.8})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Augmented & Weighted Light Model - Recall: {recall}, Accuracy: {accuracy}")'''

'''# Train the data augmentation, randomly resampled model, with class weights - Heavy
model.fit(augmented_resampled_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset,
          class_weight={0: .15, 1: 0.85})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Augmented & Resampled Heavy Model with Weights - Recall: {recall}, Accuracy: {accuracy}")'''

'''
# Train the data augmentation, randomly resampled model, with class weights - Light
model.fit(augmented_resampled_train_ds, batch_size=batch_size, epochs=10, validation_data=test_dataset,
          class_weight={0: .25, 1: 0.75})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Augmented & Resampled Light Model with Weights - Recall: {recall}, Accuracy: {accuracy}")'''


'''### Tune Final Dataset + Model'''

# Dataset alteration hyperparameters
# under_proportion = .7
# over_proportion = .3
# augment_proportion = .3

# # Random Sampling Testing
# tune_undersampled_non_fraud = randomly_undersample(train_not_fraud_images, under_proportion)
# tune_oversampled_fraud = randomly_oversample(train_fraud_images, over_proportion)
# tune_undersampled_non_fraud_ds = to_ds(tune_undersampled_non_fraud, 0)
# tune_oversampled_fraud_ds = to_ds(tune_oversampled_fraud, 1)

# # Data augmentation on randomly resampled dataset
# tune_augmented_resampled_train_fraud_ds = augment_data(oversampled_fraud_ds, augment_proportion)
# tune_augmented_resampled_train_ds = tune_augmented_resampled_train_fraud_ds.concatenate(tune_undersampled_non_fraud_ds).shuffle(
#     buffer_size=7000).batch(batch_size)

# # Train the data augmentation, randomly resampled model, with class weights - Heavy
# model.fit(tune_augmented_resampled_train_ds, batch_size=batch_size, epochs=16, validation_data=test_dataset,
#           shuffle=True, class_weight={0: .3, 1: 0.7})
# recall, accuracy = evaluate_model(model, test_dataset)
# print(f"Tuned Augmented & Resampled Model with Weights 3 - Recall: {recall}, Accuracy: {accuracy}")

# '''###Save Model'''
# # Save entire model to a single file
# model.save('fraud_model_single_file1.h5')

# Dataset alteration hyperparameters
under_proportion = .7
over_proportion = .3
augment_proportion = .3

# Random Sampling Testing
tune_undersampled_non_fraud = randomly_undersample(train_not_fraud_images, under_proportion)
tune_oversampled_fraud = randomly_oversample(train_fraud_images, over_proportion)
tune_undersampled_non_fraud_ds = to_ds(tune_undersampled_non_fraud, 0)
tune_oversampled_fraud_ds = to_ds(tune_oversampled_fraud, 1)

# Data augmentation on randomly resampled dataset
tune_augmented_resampled_train_fraud_ds = augment_data(oversampled_fraud_ds, augment_proportion)
tune_augmented_resampled_train_ds = tune_augmented_resampled_train_fraud_ds.concatenate(tune_undersampled_non_fraud_ds).shuffle(
    buffer_size=7000).batch(batch_size)

# Train the data augmentation, randomly resampled model, with class weights - Heavy
model.fit(tune_augmented_resampled_train_ds, batch_size=batch_size, epochs=16, validation_data=test_dataset,
          shuffle=True, class_weight={0: .3, 1: 0.7})
recall, accuracy = evaluate_model(model, test_dataset)
print(f"Tuned Augmented & Resampled Model with Weights 2 - Recall: {recall}, Accuracy: {accuracy}")

'''###Save Model'''
# Save entire model to a single file
model.save('fraud_model_single_file2.h5')

model = tf.keras.models.load_model('fraud_model_single_file2.h5')

# Step 2: Convert the model to TensorFlow Lite format
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Step 3: Save the TensorFlow Lite model to disk
with open('fraud_model.tflite', 'wb') as f:
    f.write(tflite_model)

print("Model has been converted and saved to 'fraud_model.tflite'")



# Dataset alteration hyperparameters
# under_proportion = .7
# over_proportion = .3
# augment_proportion = .3

# # Random Sampling Testing
# tune_undersampled_non_fraud = randomly_undersample(train_not_fraud_images, under_proportion)
# tune_oversampled_fraud = randomly_oversample(train_fraud_images, over_proportion)
# tune_undersampled_non_fraud_ds = to_ds(tune_undersampled_non_fraud, 0)
# tune_oversampled_fraud_ds = to_ds(tune_oversampled_fraud, 1)

# # Data augmentation on randomly resampled dataset
# tune_augmented_resampled_train_fraud_ds = augment_data(oversampled_fraud_ds, augment_proportion)
# tune_augmented_resampled_train_ds = tune_augmented_resampled_train_fraud_ds.concatenate(tune_undersampled_non_fraud_ds).shuffle(
#     buffer_size=7000).batch(batch_size)

# Train the data augmentation, randomly resampled model, with class weights - Heavy
# model.fit(tune_augmented_resampled_train_ds, batch_size=batch_size, epochs=16, validation_data=test_dataset,
#           shuffle=True, class_weight={0: .3, 1: 0.7})
# recall, accuracy = evaluate_model(model, test_dataset)
# print(f"Tuned Augmented & Resampled Model with Weights 1 - Recall: {recall}, Accuracy: {accuracy}")

# '''###Save Model'''
# # Save entire model to a single file
# model.save('fraud_model_single_file3.h5')

"""### Evaluation"""
# Define a function to get predicted classes from probabilities based on a threshold

# Evaluate recall for each model on the testing set
# Predict probabilities for each model
