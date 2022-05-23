import cv2
import numpy as np
import os, random
import base64

RESIZE_H = 45 # Hardcoded to match dimensions of handwritten dataset
RESIZE_W = 45 # Hardcoded to match dimensions of handwritten dataset
PADCOLOUR = 0

project_root = os.path.dirname(os.path.abspath(__file__))
DATA_DIR     = project_root + '/equation_images'


##################################################################################
#                                                                                #
#                            DATA AUGMENTATION API                               #
#                                                                                #
##################################################################################

def get_overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def get_cropped_img(input_image):
    # To invert the text to white
    input_image_cpy = input_image.copy()
    input_image_cpy = 255*(input_image_cpy < 128).astype(np.uint8)

    # Find all non-zero points
    coords = cv2.findNonZero(input_image_cpy)

    # Find minimum spanning bounding box
    x, y, w, h = cv2.boundingRect(coords)

    # Crop the image
    return input_image[y: y+h, x: x+w]


def detect_contours(input_image):
    # Make a copy to draw bounding box
    input_image_cpy = input_image.copy()

    # Convert the grayscale image to binary (image binarization opencv python), then invert
    binarized = cv2.adaptiveThreshold(input_image_cpy, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 2)
    inverted_binary_img = ~binarized

    # Detect contours
    # hierarchy variable contains information about the relationship between each contours
    contours_list, hierarchy = cv2.findContours(inverted_binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    l = []
    for c in contours_list:
        x, y, w, h = cv2.boundingRect(c)
        l.append([x, y, w, h])

    # Check whether any overlapping rectangles. We do this in a way such that we only compare each box once with all other boxes.
    lcopy = l.copy()
    keep = []
    while len(lcopy) != 0:
        curr_x, curr_y, curr_w, curr_h = lcopy.pop(0) # Look at next box
        if curr_w * curr_h < 20: # remove very small boxes. Currently this is arbitrary.
            continue
        throw = []
        for i, (x, y, w, h) in enumerate(lcopy):
            curr_interval = [curr_x, curr_x+curr_w]
            next_interval = [x, x+w]
            if get_overlap(curr_interval, next_interval) > 1 : # more than 3 pixels overlap, this is arbitrary
                # Merge the two intervals
                new_interval_x = [min(curr_x, x), max(curr_x+curr_w, x+w)]
                new_interval_y = [min(curr_y, y), max(curr_y+curr_h, y+h)]
                newx, neww = new_interval_x[0], new_interval_x[1] - new_interval_x[0]
                newy, newh = new_interval_y[0], new_interval_y[1] - new_interval_y[0]
                curr_x, curr_y, curr_w, curr_h = newx, newy, neww, newh
                throw.append(i) # Mark this box to throw away later, since it has now been merged with current box
        for ind in sorted(throw, reverse=True): # Sort in reverse order otherwise we will pop incorrectly
            lcopy.pop(ind)
        keep.append([curr_x, curr_y, curr_w, curr_h]) # Keep the current box we are comparing against
    return keep


def resize_pad(img, size, padColor=255):
    h, w = img.shape[:2]
    sh, sw = size

    # interpolation method
    if h > sh or w > sw: # shrinking image
        interp = cv2.INTER_AREA
    else: # stretching image
        interp = cv2.INTER_CUBIC

    # aspect ratio of image
    aspect = w/h  # if on Python 2, you might need to cast as a float: float(w)/h

    # compute scaling and pad sizing
    if aspect > 1: # horizontal image
        new_w = sw
        new_h = np.round(new_w/aspect).astype(int)
        pad_vert = (sh-new_h)/2
        pad_top, pad_bot = np.floor(pad_vert).astype(int), np.ceil(pad_vert).astype(int)
        pad_left, pad_right = 0, 0
    elif aspect < 1: # vertical image
        new_h = sh
        new_w = np.round(new_h*aspect).astype(int)
        pad_horz = (sw-new_w)/2
        pad_left, pad_right = np.floor(pad_horz).astype(int), np.ceil(pad_horz).astype(int)
        pad_top, pad_bot = 0, 0
    else: # square image
        new_h, new_w = sh, sw
        pad_left, pad_right, pad_top, pad_bot = 0, 0, 0, 0

    # set pad color
    if len(img.shape) is 3 and not isinstance(padColor, (list, tuple, np.ndarray)): # color image but only one color provided
        padColor = [padColor]*3

    # scale and pad
    scaled_img = cv2.resize(img, (new_w, new_h), interpolation=interp)
    scaled_img = cv2.copyMakeBorder(scaled_img, pad_top, pad_bot, pad_left, pad_right, borderType=cv2.BORDER_CONSTANT, value=padColor)
    return scaled_img


def binarize(img):
    binarized = cv2.adaptiveThreshold(img,255,cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY,11,2)
    return ~binarized


def random_sample_file():
    #  Randomly selects a file from a directory
    n=0
    random.seed();
    for root, dirs, files in os.walk(DATA_DIR):
        for name in files:
            n += 1
            if random.uniform(0, n) < 1:
                rfile=os.path.join(root, name)
    return rfile


def get_augmented_data(input_image):
    # Processing image file
    input_image = get_cropped_img(input_image)
    bounding_box_coords = detect_contours(input_image)
    inverted_binary_img = binarize(input_image)

    imgs = None
    for (x, y, w, h) in sorted(bounding_box_coords, key = lambda x: x[0]):
        img = resize_pad(inverted_binary_img[y:y+h, x:x+w], (RESIZE_H, RESIZE_W), PADCOLOUR)
        img = np.expand_dims(np.expand_dims(img, axis=0), axis=-1)
        imgs = np.array(img) if imgs is None else np.append(imgs, img, axis=0)
    return imgs


def get_test_data():
    # Randomly pick an input equation image from a data folder.
    img_path = random_sample_file()
    input_image = cv2.imread(img_path, 0)
    imgs_test_data = get_augmented_data(input_image)
    return imgs_test_data


##################################################################################
#                                                                                #
#                             ENCODE / DECODE API                                #
#                                                                                #
##################################################################################

def random_b64encoded_str():
    img_path = random_sample_file()
    b64encoded_str = ''
    with open(img_path, "rb") as image_file:
        b64encoded_str = base64.b64encode(image_file.read())
    return b64encoded_str


def convert_b64encoded_to_img(img_data, img_file):
    with open(img_file, "wb") as fh:
        fh.write(base64.decodebytes(img_data))




