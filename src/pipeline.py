"""Pipeline Module.

------------------

Algorithms used to process data before modeling.

...

A set of algorithms used to feed in and process
data before used within the model. This will contain
the data extraction from its rawest form and output
the final form of the data set. The main source of
data will be image related from the Cancer Imaging
Archive.
"""
import os
import pathlib
import json
from collections import defaultdict

import numpy as np
import pandas as pd
from pydicom import dcmread
from PIL import Image
from pydicom.errors import InvalidDicomError
import torch
from torch import optim, nn
from torch.utils import data
from torchvision import datasets, transforms

from models import BasicImageClassifier

##The dataset had duplicates due to images without any data provided on the clinical analysis. Some images were taken without clinical data for the purpose of simply taking the image. Nothing was identified for these and therefore these should be removed from  the dataset before converting the .dcm files into .png files.
def _main():
    """Test the new functions."""
    fn__test_img= "data/Dataset_BUSI_with_GT/benign/benign (1).png"
    model = BasicImageClassifier()
    loss_fn = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.parameters(), lr=0.001, momentum=0.9)
    trainer = TrainModel(model, optimizer, loss_fn)
    #Gather the data.
    tforms = transforms.Compose([transforms.Resize((512, 512)), transforms.ToTensor()])
    fn__train_dataset = "data/Chest_CT_Scans/train/"
    train_dataset = datasets.ImageFolder(fn__train_dataset, transform=tforms)
    trainloader = data.DataLoader(train_dataset, batch_size=8)
    trainer.train(trainloader, 10)


def gather_segmentation_images(filename:str, paths:str):
    """Get all of the Images with Segmentations.

    Gathers all of the image slices together with the
    respective segmentations. As this only uses the Patient
    ID as the unique identifier, only one of the folders
    after the patient id directory will be chosen together
    with the image slices. The most consistent folder may
    be used as all patients will share this folder.

    Parameter(s)
    ------------

    filename : string
        filename containing the training data set with the
        bounding boxes, and the slices or range of slices.

    paths : string
        text file containing all of the paths to the image
        files or slices.
    """
    df = pd.read_csv(filename)
    with open(paths, 'r') as fp:
        list__paths = fp.readlines()
        fp.close()
    for _, row in df.iterrows():
        patient_folder = list(filter(lambda x: row['Patient ID'] in x, list__paths))
        print(patient_folder)
        exit()

def _extract_feature_definitions(filepath:str, savepath:str, l:int):
    df = pd.read_csv(filepath)
    features = df.iloc[:l]
    feats = features.fillna("blank")
    with open(savepath, 'w') as fp:
        json.dump(feats, fp)
        fp.close()

def _remove_first_row(filepath:str, nfilepath:str):
    xls = pd.ExcelFile(filepath, engine='xlrd')
    df = pd.read_excel(xls, 0)
    df.to_csv(filepath, index=False)
    with open(filepath, 'r') as file:
        data = file.read()
    new_data = data.split('\n', 1)[-1]
    with open(nfilepath, 'w') as fp:
        fp.write(new_data)

def _convert_dicom_to_png(filename:str) -> None:
    """Convert a list of dicom files into their png forms.

    ...
    """
    df = pd.read_csv(filename)
    for _, row in df.iterrows():
        ds = dcmread(row['paths'])
        path = pathlib.PurePath(row['paths'])
        dicom_name = path.name
        name = dicom_name.replace(".dcm", "")
        new_image = ds.pixel_array.astype(float)
        scaled_image = (np.maximum(new_image, 0) / new_image.max()) * 255
        scaled_image = np.uint8(scaled_image)
        final_image = Image.fromarray(scaled_image)
        final_image.save(f"data/CMMD-set/classifying_set/raw_png/{row['Subject ID'] + '_' + name + ds.ImageLaterality}.png")
    return None

def extract_key_images(data_dir:str, metadata_filename:str, new_download = False):
    """Extract the key images based on the Annotation Boxes file.

    ...

    Grabs the images from the full directory and
    moves them to a separate directory for keeping
    only the key data.
    """
    if not new_download:
        return None
    else:
        df__metadata = pd.read_csv(metadata_filename)
        root_path = os.getcwd()
        root_path = root_path.replace("//", "/")
        img_paths_list = list()
        for _, row in df__metadata.iterrows():
            PID = row["Subject ID"]
            file_location = row["File Location"]
            file_location = file_location.replace("//","/").lstrip(".")
            file_location = root_path + data_dir + file_location
            imgs = os.listdir(file_location)
            for img in imgs:
                ds = dcmread(file_location + '/' + img)
                img_paths = {
                    'ID1': PID,
                    'paths': file_location + '/' + img,
                    'LeftRight': ds.ImageLaterality
                }
                img_paths_list.append(img_paths)
        df_img_paths = pd.DataFrame(img_paths_list)
        return df_img_paths

def extract_dicom_data(file, target_data:list =[]) -> dict:
    """Extract the data from the .dcm files.

    ...

    Reads each independent file using the pydicom
    library and extracts key information, such as
    the age, sex, ethnicity, weight of the patient,
    and the imaging modality used.

    Parameters
    ---------
    file : Unknown
        Either the path to the file or the file itself.
        In the case that the .dcm file is already
        loaded, the algorithm will proceed to extract
        the data. Otherwise, the algorithm will load
        the .dcm file and extract the necessary data.

    target_data : List
        This contains all of the tag names that will be
        used as part of the data extraction. In the case
        that the list is empty, then only the image will be
        used.

    Returns
    -------
    datapoint : dictionary
        Dictionary comprised of the image data
        (numpy array), and the metadata associated
        with the DICOM file as its own separate
        `key:value` pair. This only pertains to the
        patient data and NOT the metadata describing
        how the image was taken.

    Raises
    ------
    InvalidDicomError
        The file selected for reading is not a DICOM
        or does not end in .dcm. Set in place to
        stop the algorithm in the case that any other
        filetype is introduced. Causes an error to be
        printed and the program to exit.

    AttributeError
        Occurs in the case that the DICOM file does
        not contain some of the metadata used for
        classifying the patient. In the case that
        the metadata does not exist, then the model
        continues on with the classification and some
        plots may be missing from the second page.
    """
    datapoint = dict()
    if type(file) == str:
        try:
            ds = dcmread(file)
            datapoint['Full Location'] = file
        except (InvalidDicomError) as e:
            print(f"ERROR: The file {file} is not a DICOM file and therefore cannot be read.")
            print(e)
            exit()
    else:
        ds = file

    slices = np.asarray(ds.pixel_array).astype('float32')
    #slices = da.asarray(ds.pixel_array).astype('float32')
    #slices = (slices - np.min(slices)) / (np.max(slices) - np.min(slices))
    if target_data == []:
        pass
    else:
        for target in target_data:
            if target in ds:
                datapoint[str(target)] = ds[target].value
            else:
                pass

    if slices.ndim <= 2:
        pass
    elif slices.ndim >= 3:
        slices = slices[0]
    slices = slices[..., np.newaxis]
    datapoint['image'] = slices
    datapoint['Patient ID'] = ds.PatientID
    return datapoint

def load_image(filename:str, size:tuple) -> np.ndarray:
    """Load the image based on the path.

    ------------------------------------

    Parameter
    ---------
    filename : string
        string containing the relative or absolute path to
        the image.

    size : tuple
        List containing the desired width and height to
        readjust the image.
    Returns
    -------
    data : numpy Array
        Returns a 3D array containing the image of the
        dimensions (width, height, colors).
    """
    img = Image.open( filename ).convert('L')
    img = img.resize(size)
    img.load()
    if 'mask' in filename:
        data = np.asarray( img ).astype('int32')
    else:
        raw_data = np.asarray( img ).astype('float32')
        data = (raw_data - np.min(raw_data)) / (np.max(raw_data) - np.min(raw_data))
    if data.ndim == 2:
        data = data[np.newaxis, ...]
    else:
        pass
    return data

def merge_dictionaries(*dictionaries) -> dict:
    """Merge n number of dictionaries.
    
    ----------------------------------

    Merge any number of dictionary within the variable.
    """
    mdictionary = defaultdict()
    for dictionary in dictionaries:
        for key, value in dictionary.items():
            if key not in mdictionary:
                mdictionary[key] = [value]
            else:
                mdictionary[key].append(value)
    return mdictionary

def transform_dicom_data(datapoint:dict, definitions:dict) -> dict:
    """Transform the data into an format that can be used for displaying and modeling.

    ...
    Transforms the textual categorical data into numerical
    to input the data into the machine learning model. This
    function depends upon two dictionaries, one containing
    the data and the other a set of references that can be
    used to transform the textual categorical values into
    the numerical values. This function also removes the
    area of the image that contains columns whose values
    are zero.
    Parameters
    ----------
    datapoint : dictionary
        Contains the image and related metadata in
        `key:value` pair format.
    definitions : dictionary
        Set of values found within the data point and their
        definitions. This will contain the column value and
        the meaning of each categorical value. The nature
        of this could be the following:
        EX.: {
            key:{
                "category":1
                }
            }
    Returns
    -------
    datapoint : dictionary
        same dictionary with the categorical data
        transformed into numerical (from text).
    Raises
    ------
    AttributeError
        Indicator of the `key` does not exists.
    KeyError
        Indicator of the `key` does not exists.
    """
    for key, values in definitions.items():
        if key in datapoint.keys():
            datapoint[key] = values[datapoint.get(key)]
        else:
            print(f'WARNING: Indicator "{key}" could not be found within the data point.')
    try:
        img = datapoint['image']
        img = img[:, ~np.all(img == 0, axis = 0)]
        img_mod = rescale_image(img)
        datapoint['image'] = img_mod
    except (AttributeError, KeyError):
        print('WARNING: Indicator "image" does not exist.')
    return datapoint

def balance_data(df:pd.DataFrame, columns:list=[],sample_size:int=None) -> pd.DataFrame:
    """Balance data for model training.

    Splits the dataset into groups based on the categorical
    columns provided. The function will use a for loop to
    extract samples based on predetermined categories. a
    list of permutations will be used.

    Parameter(s)
    ------------
    df : Pandas DataFrame
        Contains all of the data necessary to load the
        training data set.
    columns : list
        List of columns which will be used to categorize
        the data. In the case that the columns list is
        empty, then the dataset will simply be resampled.
    sample_size : integer
        Describes the sample size of the dataset that
        will be used for either training or testing the
        machine learning model.
    Returns
    -------
    df_balanced : Pandas DataFrame
        Balanced data set ready for feature extraction.
    """
    assert sample_size != 0, "The sample size cannot be zero."
    if sample_size == None:
        sample_size = len(df)
    else:
        pass

    if columns == []:
        df_balanced = df.sample(n=sample_size, random_state=42)
    else:
        groups = df.groupby(columns)
        number_groups = len(groups.groups)
        sample_group_size = int(sample_size / number_groups)
        sampled_groups = list()
        diff_sample_size = 0
        for gtype, df_group in groups:
            fgroup = sample_group_size + diff_sample_size
            if len(df_group) >= fgroup:
                df__selected_group = df_group.sample(n=int(fgroup), random_state=42)
            elif len(df_group) >= sample_group_size:
                df__selected_group = df_group.sample(n=int(sample_group_size), random_state=42)
            elif fgroup <= 0:
                break
            else:
                df__selected_group = df_group.sample(n=int(len(df_group)), random_state=42)
            sampled_groups.append(df__selected_group)
            diff_sample_size += sample_group_size - len(df__selected_group)
        df_balanced = pd.concat(sampled_groups)
    return df_balanced

def load_training_data(filename:str, pathcol:str, balance:bool=True, sample_size:int=1_000, cat_labels:list=[]):
    """Load the DICOM data as a dictionary.

    ...

    Creates a dictionary containing three different
    numpy arrays. The first array is comprised of
    multiple DICOM images, the second contains the
    categorical data as a vector, and the third contains
    the classification in numerical form.

    Parameters
    ----------
    filename : String
        path to a file which contains the metadata,
        classification, and path to the DICOM file.
        Will also contain some sort of ID to better
        identify the samples.

    validate : Boolean
        Conditional statement that determines whether the
        data requires a split between training and
        validation. In the case that this is False, then
        the data set is not split between training and
        validation.

    cat_labels : unknown
        Contains all of the labels that will be used within
        the training set. These labels are meant to be the
        column names of the categorical values that will be
        used for training the machine learning model.
    Returns
    -------
    data : dictionary
        Dictionary containing the encoded values
        for the metadata and the transformed image
        for input to the model.
    """
    if type(filename) == str:
        df = pd.read_csv(filename)
    elif type(filename) == pd.DataFrame:
        df = filename
    else:
        print("There was some error.")
        exit()
    #data = dict()
    if balance == True:
        df_balanced = balance_data(df, sample_size=sample_size)
    else:
        df_balanced = df.sample(n=sample_size, random_state=42)

    if bool(cat_labels) == False:
        data = map(extract_data, df_balanced[pathcol])
        df = pd.DataFrame(list(data))
        df_full = pd.merge(df_balanced, df, on=pathcol)
        return df_full
    elif bool(cat_labels) == True:
        full_labels = cat_labels * len(cat_labels) * len(df_balanced)
        data = map(extract_data, df_balanced[pathcol], full_labels)
        df = pd.DataFrame(list(data))
        df_full = pd.merge(df, df_balanced, on=pathcol)
        return df_full
    else:
        print('None of the conditions were met')
        exit()

def  load_testing_data(filename:str, sample_size= 1_000) -> pd.DataFrame:
    """Load the data used  for testing.

    Loads a dataset to be fed into the model for making
    predictions. The output of the testing data will be
    comprised of a dictionary that can be fed directly into
    the model.

    Parameter(s)
    ------------
    filename : str
        path to file containing the file paths to test data.

    Returns
    -------
    df__test : Pandas DataFrame
        Contains the all of the data necessary for testing.
    """
    df = pd.read_csv(filename)
    df = df.dropna(subset=['classification'])
    df = df.sample(n=sample_size, random_state=42)
    print("iterating through {} rows...".format(len(df)))
    dfp_list = list()
    for _, row in df.iterrows():
        datapoint = extract_data(row['paths'])
        datapoint = transform_data(datapoint)
        drow = row.to_dict()
        datapoint.update(drow)
        dfp_list.append(datapoint)
    tdata = pd.DataFrame(dfp_list)
    return tdata

def rescale_image(img:np.ndarray) -> np.ndarray:
    """Rescale the image to a more manageable size.

    Changes the size of the image based on the length and
    width of the image itself. This is to reduce the amount
    of computations required to make predictions based on
    the image.

    Parameter(s)
    ------------
    img : Numpy Array
        array containing the raw values of images.
    """
    size = img.shape
    width = int(size[1] / 2)
    height = int(size[0] / 2)
    img = img.astype(float)
    scaled_image = (np.maximum(img, 0) / img.max()) * 255
    scaled_image = np.uint8(scaled_image)
    final_image = Image.fromarray(scaled_image)
    final_image = final_image.resize(size=(width, height))
    img_mod = np.asarray(final_image)
    img_mod = np.asarray([img_mod])
    img_mod = np.moveaxis(img_mod, 0, -1)
    return img_mod

def calculate_confusion_matrix(fin_predictions:pd.DataFrame):
    """Calculate the confusion matrix using pandas.

    Calculates the confusion matrix using a csv file that
    contains both the predictions and actual labels. This
    function then creates a crosstab of the data to develop
    the confusion matrix.

    Parameter(s)
    ------------
    fin_predictions : Pandas DataFrame
        DataFrame containing the prediction and actual
        labels.

    Returns
    -------
    ct : Pandas DataFrame
        Cross tab containing the confusion matrix of the
        predictions compared to the actual labels.

    metrics : Dictionary
        Contains the basic metrics obtained from the
        confusion matrix. The metrics are the following:
        - Accuracy
        - Precision
        - Recall
        - F1 Score
    """
    ct = pd.crosstab(fin_predictions['pred_class'], fin_predictions['classification'])
    print(ct)
    # Set the initial values
    tp = ct.values[1][1]
    tn = ct.values[0][0]
    fn = ct.values[0][1]
    fp = ct.values[1][0]
    # Calculate the metrics
    metrics = dict()
    metrics['Accuracy'] = (tp + tn) / (tp + tn + fp + fn) # Ability of model to get the correct predictions
    metrics['Precision'] = tp / (tp + fp) # Ability of model to label actual positives as positives (think retrospectively)
    metrics['Recall'] = tp / (tp + fn) # Ability of model to correctly identify positives
    metrics['F1 Score'] = (2 * metrics['Precision'] * metrics['Recall']) / (metrics['Precision'] + metrics['Recall'])
    return ct, metrics


class ImageSet(data.Dataset):
    """
    Dataset extracted from paths to cancer images.

    ...

    Dataset subclass that will grab the path to a folder
    containing the entire set of images and if images are
    organized based on folders, then it will attach a label.
    The label will be numerical and represent the origin of the
    folder.
    *Alternatively, one can use the torchvision.data.ImageFolder class for the same reason.
    """

    def __init__(self, root='train/', image_loader=None, transform=None):
        """Initialize the Dataset Subclass."""
        self.root = root
        self.folders = os.listdir(root)
        self.files = list()
        self.dict__files = dict()
        for folder in self.folders:
            fold = os.path.join(self.root, folder)
            self.dict__files[folder] = os.listdir(fold)
            self.files.extend(os.listdir(fold))
        self.loader = image_loader
        self.transform = transform

    def __len__(self):
        """Get the Length of the items within the dataset."""
        return sum([len(self.files)])

    def __getitem__(self, index):
        """Get item from class."""
        images = [self.loader(os.path.join(self.root, folder)) for folder in self.folders]
        if self.transform is not None:
            images = [self.transform(img) for img in images]
        return images


class TrainModel:
    """
    Class for training pytorch machine learning models.

    This class functions as an environment for training the
    pytorch models.
    """

    def __init__(self, model, optimizer, loss):
        """Initialize the class."""
        self.model = model
        self.opt = optimizer
        self.criterion = loss

    def get_model(self):
        """Get the Model post training."""
        return self.model

    def train(self, trainloader:data.DataLoader, epochs:int, gpu=False):
        """Train the machine learning model."""
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        print("The model wil lbe running on ", device, "device")
        self.model.to(device)
        for epoch in range(epochs):
            running_loss = 0.0
            for i, (inputs, labels) in enumerate(trainloader, 0):
                inputs = inputs.to(device)
                labels = labels.to(device)
                self.opt.zero_grad()

                outputs = self.model(inputs)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.opt.step()

                running_loss += loss.item()
                if i % 10 == 9:
                    print(f'[{epoch + 1}, {i + 1:5d}] loss: {running_loss / 10:.3f}')
                    running_loss = 0.0


if __name__ == "__main__":
    _main()
