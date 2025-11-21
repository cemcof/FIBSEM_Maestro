import logging
import math
from scipy.ndimage.measurements import label
import numpy as np
from skimage.measure import regionprops
from scipy.optimize import curve_fit
import cv2
from scipy import ndimage

def center_padding(image, goal_size):
    """ Add padding to goal_size. The image will be in the center of final image"""
    d_height = image.shape[0] - goal_size[0]
    d_width = image.shape[1] - goal_size[1]

    # do not pad if image is bigger than goal_size
    if d_height < 0:
        d_height = 0
    if d_width < 0:
        d_width = 0

    pad_height = math.ceil(d_height / 2)
    pad_width = math.ceil(d_width / 2)
    output_image = np.pad(image, ((pad_height, pad_height), (pad_width, pad_width)), mode='constant')
    # crop if needed
    if output_image[0] != goal_size[0] or output_image[1] != goal_size[1]:
        output_image = output_image[:goal_size[0],:goal_size[1]]
    return output_image


def center_cropping(image, goal_size):
    """ The image will be cropped in the center to the size of final image"""
    d_height = goal_size[0] - image.shape[0]
    d_width = goal_size[1] - image.shape[1]

    # do not crop if image is smaller than goal_size
    if d_height < 0:
        d_height = 0
    if d_width < 0:
        d_width = 0

    pad_height = math.floor(d_height / 2)
    pad_width = math.floor(d_width / 2)
    output_image = np.copy(image)
    output_image = output_image[pad_height:pad_height+goal_size[0],pad_width:pad_width+goal_size[1]]
    return output_image


blobs_structure = np.ones((3, 3), dtype=np.int8)


def find_blobs(image):
    labeled_image, _ = label(image, blobs_structure)
    return labeled_image


def filter_blobs_min_area(labeled_image, min_area):
    # filter small blobs
    assert min_area is not None

    # Calculate the area of each blob
    blob_areas = np.bincount(labeled_image.ravel())
    # Create a mask for blobs that have area greater than the defined min_area
    mask = np.isin(labeled_image, np.where(blob_areas > min_area)[0])
    # Apply the mask to the image,
    # This will set pixels in blobs with area <= min_area to 0
    filtered_image = labeled_image * mask
    labeled_mask, _ = label(filtered_image, blobs_structure)
    return labeled_mask

def find_central_blob_label(labeled_image):
    """ Find the label closest to the image center"""
    # Get number of labels
    num_labels = labeled_image.max()

    # Define image center
    center = np.array(labeled_image.shape) / 2

    min_dist = np.inf
    central_label = None

    # Iterate over each label
    for label in range(1, num_labels + 1):
        # Find pixels with current label
        pixels = np.transpose(np.where(labeled_image == label))

        # Compute centroid of current labeled region
        centroid = pixels.mean(axis=0)

        # Compute distance from centroid to center
        dist = np.linalg.norm(center - centroid)

        # If it's closer to the center than what we've found so far
        if dist < min_dist:
            min_dist = dist
            central_label = label

    return central_label

def blob_center(labeled_image):
    """ Return center of labeled image (closest to center of FoV)"""
    central_blob = find_central_blob_label(labeled_image)
    properties = regionprops(labeled_image)
    return properties[labeled_image].centroid[1], properties[labeled_image].centroid[0]


def largest_rectangles_in_blobs(self, labeled_image):
    """ Get the largest possible rectangle that fits to blobs"""
    num_features = np.max(labeled_image.ravel())
    rectangles = []

    # Iterate over each found feature
    for feature in range(1, num_features + 1):

        # Create a binary mask for the current feature
        feature_mask = np.array(labeled_image == feature).astype(int)

        # Initialize the DP table and variables to hold the max area and
        # coordinates of max rectangle
        dp = np.zeros_like(feature_mask, dtype=int)
        max_area = 0
        max_rect = (0, 0, 0, 0)  # x1, y1, x2, y2

        for i in range(feature_mask.shape[0]):
            for j in range(feature_mask.shape[1]):
                if feature_mask[i, j] == 0:
                    dp[i, j] = 0
                else:
                    dp[i, j] = dp[i - 1, j] + 1 if i > 0 else 1
                m = dp[i, j]
                for k in range(j, -1, -1):
                    if dp[i, k] == 0:
                        break
                    m = min(m, dp[i, k])
                    area = m * (j - k + 1)
                    if area > max_area:
                        max_area = area
                        max_rect = (k, i - m + 1, j, i)

        rectangles.append(max_rect)
    return rectangles


def crop_image(image, rectangle):
    y1, x1, y2, x2 = rectangle
    cropped_image = image[y1:y2, x1:x2]
    return cropped_image


def get_stripes(img, separate_value=10, minimal_stripe_height=5):
    """ Get stripes of image separated by black lines (<separate_value)"""
    # identify the blank spaces
    x_proj = np.sum(img, axis=0)  # identify blank line by min function
    zero_pos = np.where(x_proj < separate_value)[0]  # position of all blank lines
    # go through the sections
    image_section_index = 0  # actual image section
    for i in range(len(zero_pos) - 1):  # iterate all blank lines - find the image section
        x0 = zero_pos[i]
        x1 = zero_pos[i + 1]
        # if these 2 blank lines are far from each other (it makes the image section)
        if x1 - x0 >= minimal_stripe_height:
            bin = np.arange(x0 + 1, x1 - 1)  # list of stripe indices
            yield image_section_index, bin
            image_section_index += 1


def image_saturation_info(image):
    """ How many (in fraction) pixels are saturated or zeroed"""
    max_value = 2 ** image.bit_depth - 1
    total_px = len(image.data)  # total number of pixels
    saturated_px = np.sum(image.data == max_value)
    zeroed_px = np.sum(image.data == 0)
    saturated_frac = saturated_px / total_px
    zeroed_frac = zeroed_px / total_px
    return saturated_frac, zeroed_frac


def image_bit_dept_band(image, band_min_value_frac=0.01, histogram_total_width=256):
    """Returns ratio of used of band of bit depth"""
    # band_min_value_frac - minimal number of pixels (fraction of total pixel count) considered as used band
    # histogram_total_width - histogram bins

    max_value = 2 ** image.bit_depth - 1
    band_min_value = len(image.data) * band_min_value_frac  # minimal number of pixels, that will be considered as used band
    histogram, bin_edges = np.histogram(image.data, bins=histogram_total_width, range=[0, max_value])

    # Find the minimum and maximum non-zero bins
    min_bin = next((i for i, count in enumerate(histogram) if count > band_min_value), None)
    max_bin = len(histogram) - 1 - next((i for i, count in enumerate(reversed(histogram)) if count > band_min_value), None)

    # The "width" of the histogram would be:
    histogram_width = max_bin - min_bin + 1
    return histogram_width / histogram_total_width  # return the fraction band of used gray levels


def prepare_image(image, blur=0):
    if np.min(image) < 0:
        image[image<0] = 0
        logging.warning('Processed image is below zero -> correcting by clipping')
    if np.max(image) < 255:
        image[image>255] = 255
        logging.warning('Processed image is above 8bit band -> correcting by clipping')
    img = np.asarray(image, np.uint8)
    if blur > 0:
        img = ndimage.gaussian_filter(img, sigma=int(blur))
    return img

def template_matching(template, image, blur, return_heatmap=False):
    result = cv2.matchTemplate(prepare_image(image, blur), prepare_image(template, blur), cv2.TM_CCOEFF_NORMED)
    (minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(result)  # cv2.minMaxLoc returns [y, x]
    logging.info(f'Template matching confidence: {maxVal}')

    dx = maxLoc[1] - result.shape[0] // 2
    dy = maxLoc[0] - result.shape[1] // 2

    if return_heatmap:
        return dx, dy, maxVal, result
    else:
        return dx, dy, maxVal


# Define a Gaussian function
def gauss(x, *p):
    a, b, c, d = p
    y = a * np.exp(-np.power((x - b), 2.) / (2. * c ** 2.)) + d
    return y


def shift_sift(image, template, blur):
    # Load the images in grayscale
    img1 = prepare_image(image, blur)
    img2 = prepare_image(template, blur)

    # Ensure images are loaded
    if img1 is None or img2 is None:
        raise ValueError("One or both of the images could not be loaded")

    # Initialize SIFT detector
    sift = cv2.SIFT_create()

    # Compute SIFT keypoints and descriptors
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    # Initialize BFMatcher
    bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)

    # Match descriptors
    matches = bf.match(des1, des2)

    # Sort them in the order of their distance.
    matches = sorted(matches, key=lambda x: x.distance)[:20]  # best 20

    # Draw first 10 matches
    #img3 = cv2.drawMatches(img1, kp1, img2, kp2, matches, None, flags=2)
    #img3 = cv2.cvtColor(img3, cv2.COLOR_BGR2RGB)

    # Display the result
    #cv2.imshow("Matches", img3)
    # Compute the shifts
    shifts_x = [kp1[match.queryIdx].pt[0] - kp2[match.trainIdx].pt[0] for match in matches]
    shifts_y = [kp1[match.queryIdx].pt[1] - kp2[match.trainIdx].pt[1] for match in matches]

    # calculate median shift in x and y directions
    median_shift_x = np.median(shifts_x)
    median_shift_y = np.median(shifts_y)

    return None, median_shift_x, median_shift_y, 1, None

def template_matching_subpixel(image, template, blur, upsampling_factor=1, return_heatmap=True):
    """ Template matching with subpixel accuracy. It uses oversampling and gauss fitting"""
    # image upsampling
    popt = popt2 = None
    image_highres = cv2.resize(prepare_image(image, blur), None, fx=upsampling_factor, fy=upsampling_factor, interpolation=cv2.INTER_LINEAR)
    template_highres = cv2.resize(prepare_image(template, blur), None, fx=upsampling_factor, fy=upsampling_factor, interpolation=cv2.INTER_LINEAR)

    # template matching
    res = cv2.matchTemplate(image_highres, template_highres, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    # Fit Gaussian curve for y direction data
    x = np.array(range(len(res[:, max_loc[1]])))
    y = res[:, max_loc[1]].squeeze()
    # set far pixels to 0
    neighborhood = 10 * upsampling_factor
    start_index = max(0, max_loc[0] - neighborhood)
    end_index = min(len(y), max_loc[0] + neighborhood)
    y = y[start_index:end_index]
    x = x[start_index:end_index]
    try:
        popt, _ = curve_fit(gauss, x, y, p0=[max_val, max_loc[0], len(y) / 4., min_val])
        peak_x = popt[1]
    except Exception as e:
        logging.warning('Subpixel in Y axis fit failed! Precision may be compromised')
        peak_x = max_loc[0]

    # Fit Gaussian curve for x direction data
    x2 = np.array(range(len(res[max_loc[0], :])))
    y2 = res[max_loc[0], :].squeeze()
    # set far pixels to 0
    neighborhood = 10 * upsampling_factor
    start_index = max(0, max_loc[1] - neighborhood)
    end_index = min(len(y2), max_loc[1] + neighborhood)
    y2 = y2[start_index:end_index]
    x2 = x2[start_index:end_index]

    try:
        popt2, _ = curve_fit(gauss, x2, y2, p0=[max_val, max_loc[1], len(y2) / 4., min_val])
        peak_y = popt2[1]
    except Exception as e:
        logging.warning('Subpixel in X axis fit failed! Precision may be compromised')
        peak_y = max_loc[1]

    # subpixel disabled!!!
    peak_x = max_loc[1]
    peak_y = max_loc[0]

    # Convert peak location back to original resolution
    peak_x /= upsampling_factor
    peak_y /= upsampling_factor

    # Recentering
    peak_x -= res.shape[0] / upsampling_factor / 2
    peak_y -= res.shape[1] / upsampling_factor / 2

    # save y and gauss fitting
    if popt is not None and popt2 is not None:
        subpixel_log_data = [y, gauss(x, *popt), y2, gauss(x2, *popt2)]
    else:
        subpixel_log_data = None

    if return_heatmap:
        return subpixel_log_data,peak_x, peak_y, max_val, res
    else:
        return subpixel_log_data,peak_x, peak_y, max_val
