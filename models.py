"""This file will contain all of the acutalized models created from the abstract model class(es) made within the base.py file."""
from keras.layers import Conv2D, Dense, Rescaling, Flatten, MaxPooling2D, Dropout, RandomZoom, AveragePooling2D, Input, concatenate
from keras.models import Model
from keras.utils import plot_model
from keras.losses import SparseCategoricalCrossentropy
from keras.metrics import SparseCategoricalAccuracy
import pipeline as pl
import pandas as pd
from sklearn.model_selection import train_test_split
import tensorflow as tf
import numpy as np
from pipeline import load_data

def main():
    inputs, output = tumor_classifier(256,256)
    model = Model(inputs=inputs, outputs=output)
    #model.build(input_shape=(800,800))
    #plot_model(model, show_shapes=True)
    model.compile(optimizer='adam', loss=SparseCategoricalCrossentropy(from_logits=True), metrics=[SparseCategoricalAccuracy()])
    filename = "data/CMMD-set/medical_data_with_image_paths.csv"
    X, y = load_data(filename)
    Xy = tf.data.Dataset.zip((X,y))
    model.fit(Xy, epochs=10, batch_size=32)


def base_image_classifier(img_height:float, img_width:float):
    """Basic Image Classifier for model comparison improvement.

    ...

    A class containing a simple classifier for any
    sort of image. The models stemming from this
    class will function to only classify the image
    in one manner alone (malignant or non-malignant).
    This model will not contain any rescaling or 
    data augmentation to show how significant the
    accuracy between a model with rescaling and
    data augmentation is against a model without
    any of these.
    """
    img_input = Input(shape=(img_height,img_width,3), name="Image Input")
    cat_input = Input(shape=None, name="Categorical Input")
    inputs = [img_input, cat_input]
    # Set up the images
    x = Conv2D(16, 3, padding='same', activation='relu')(img_input)
    x = MaxPooling2D()(x)
    x = Flatten()(x)
    x = Dense(128, activation='relu')(x)
    #Set up the categorical data
    y = Dense(2, activation='relu')(cat_input)
    # Merge both layers
    together = concatenate([x,y])
    output = Dense(2, activation='softmax', name="output")(together)
    return inputs, output

def base_image_classifier2(img_height:float, img_width:float):
    """Basic Image Classifier with rescaling and data augmentation.

    ...

    A class containing a simple classifier for any
    sort of image. The models stemming from this class
    will include rescaling and data augmentation
    for the sake and purpose of normalizing the data.
    """
    img_input = Input(shape=(img_height,img_width,3), name="Image Input")
    cat_input = Input(shape=(5), name="Categorical Input")
    inputs = [img_input, cat_input]
    # Set up the images
    x = Rescaling(1./255, input_shape= (img_height, img_width,3))(img_input)
    x = RandomZoom(0.1)(x)
    x = Conv2D(16, 3, padding='same', activation='relu')(x)
    x = MaxPooling2D()(x)
    x = Dense(128, activation='relu')(x)
    #Set up the categorical data
    y = Dense(2, activation='relu')(cat_input)
    # Merge both layers
    together = concatenate([x,y])
    output = Dense(2, activation='softmax')(together)
    return inputs, output

def tumor_classifier(img_height:float, img_width:float):
    """Complete Tumor Classification Algorithm.

    ...

    A class containing a simple classifier for any
    sort of image. The models stemming from this class
    will include rescaling and data augmentation
    for the sake and purpose of normalizing the data.
    """
    img_input = Input(shape=(img_height,img_width,3), name="Image Input")
    cat_input = Input(shape=(2), name="Categorical Input")
    inputs = [img_input, cat_input]
    # Set up the images
    x = Rescaling(1./255, input_shape= (img_height, img_width,3))(img_input)
    x = RandomZoom(0.1)(x)
    x = Conv2D(32, 3, padding='same', activation='relu')(x)
    x = MaxPooling2D()(x)
    x = Conv2D(64, 3, padding='same', activation='relu')(x)
    x = MaxPooling2D()(x)
    x = Conv2D(64, 3, padding='same', activation='relu')(x)
    x = MaxPooling2D()(x)
    x = Flatten()(x)
    print(x)
    x = Dense(64, activation='relu')(x)
    #Set up the categorical data
    y = Dense(2, activation='relu')(cat_input)
    # Merge both layers
    together = concatenate([x,y])
    output = Dense(2, activation='softmax', name="classification")(together)
    return inputs, output


if __name__ == "__main__":
    main()