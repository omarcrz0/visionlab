
# coding: utf-8



# <codecell>

%matplotlib inline   


# <codecell>

from matplotlib import cm
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from scipy import ndimage as ndi
from scipy import stats

from skimage import exposure, feature, filters, io, measure, morphology, restoration, segmentation, util   


# <markdowncell>
# # Introduction to three-dimensional image processing
# 
# Images are represented as `numpy` arrays. A single-channel, or grayscale,
# image is a 2D matrix of pixel intensities of shape `(row, column)`. We can
# construct a 3D volume as a series of 2D `planes`, giving 3D images the shape
# `(plane, row, column)`. Multichannel data adds a `channel` dimension in the
# final position containing color information.
# 
# These conventions are summarized in the table below:
# 
# 
# |Image type|Coordinates|
# |:---|:---|
# |2D grayscale|(row, column)|
# |2D multichannel|(row, column, channel)|
# |3D grayscale|(plane, row, column)|
# |3D multichannel|(plane, row, column, channel)|
# 
# Some 3D images are constructed with equal resolution in each dimension; e.g.,
# a computer generated rendering of a sphere. Most experimental data captures
# one dimension at a lower resolution than the other two; e.g., photographing
# thin slices to approximate a 3D structure as a stack of 2D images. The
# distance between pixels in each dimension, called `spacing`, is encoded in a
# tuple and is accepted as a parameter by some `skimage` functions and can be
# used to adjust contributions to filters.
# 
# ## Input/Output and display
# 
# Three dimensional data can be loaded with `skimage.io.imread`. The data for
# this tutorial was provided by the Allen Institute for Cell Science. It has
# been downsampled by a factor of 4 in the `row` and `column` dimensions to
# reduce computational time.


# <codecell>

data = io.imread("../images/cells.tif")

print("shape: {}".format(data.shape))
print("dtype: {}".format(data.dtype))
print("range: ({}, {})".format(data.min(), data.max()))   


# <markdowncell>
# The distance between pixels was reported by the microscope used to image the
# cells. This `spacing` information will be used to adjust contributions to
# filters and helps decide when to apply operations planewise. We've chosen to
# normalize it to `1.0` in the `row` and `column` dimensions.


# <codecell>

original_spacing = (0.2900000, 0.0650000, 0.0650000)

rescaled_spacing = np.multiply((1.0, 4.0, 4.0), original_spacing)

spacing = rescaled_spacing / rescaled_spacing[1]

print("spacing: {}".format(spacing))   


# <markdowncell>
# Try visualizing the image with `skimage.io.imshow`...


# <codecell>

try:
    io.imshow(data, cmap="gray")
except TypeError as e:
    print(str(e))   


# <markdowncell>
# `skimage.io.imshow` can only display grayscale and RGB(A) 2D images. We can
# use `skimage.io.imshow` to visualize 2D planes. By fixing one axis, we can
# observe three different views of the image.


# <codecell>

def show_plane(ax, plane, cmap="gray", title=None):
    ax.imshow(plane, cmap=cmap)
    ax.set_xticks([])
    ax.set_yticks([])
    
    if title:
        ax.set_title(title)   


# <codecell>

_, (a, b, c) = plt.subplots(nrows=1, ncols=3, figsize=(16, 4))

show_plane(a, data[32], title="Plane = 32")
show_plane(b, data[:, 128, :], title="Row = 128")
show_plane(c, data[:, :, 128], title="Column = 128")   


# <markdowncell>
# Three-dimensional images can be viewed as a series of two-dimensional
# functions. The `display` helper function displays 30 planes of the provided
# image. By default, every other plane is displayed.


# <codecell>

def display(im3d, cmap="gray", step=2):
    _, axes = plt.subplots(nrows=5, ncols=6, figsize=(16, 14))
    
    vmin = im3d.min()
    vmax = im3d.max()
    
    for ax, image in zip(axes.flatten(), im3d[::step]):
        ax.imshow(image, cmap=cmap, vmin=vmin, vmax=vmax)
        ax.set_xticks([])
        ax.set_yticks([])   


# <codecell>

display(data)   


# <markdowncell>
# ## Exposure


# <markdowncell>
# `skimage.exposure` contains a number of functions for adjusting image
# contrast. These functions operate on pixel values. Generally, image
# dimensionality or pixel spacing does not need to be considered.
# 
# [Gamma correction](https://en.wikipedia.org/wiki/Gamma_correction), also known
# as Power Law Transform, brightens or darkens an image. The function $O =
# I^\gamma$ is applied to each pixel in the image. A `gamma < 1` will brighten
# an image, while a `gamma > 1` will darken an image.


# <codecell>

# Helper function for plotting histograms.
def plot_hist(ax, data, title=None):
    ax.hist(data.ravel(), bins=256)
    ax.ticklabel_format(axis="y", style="scientific", scilimits=(0, 0))
    
    if title:
        ax.set_title(title)   


# <codecell>

gamma_low_val = 0.5
gamma_low = exposure.adjust_gamma(data, gamma=gamma_low_val)

gamma_high_val = 1.5
gamma_high = exposure.adjust_gamma(data, gamma=gamma_high_val)

_, ((a, b, c), (d, e, f)) = plt.subplots(nrows=2, ncols=3, figsize=(12, 8))

show_plane(a, data[32], title="Original")
show_plane(b, gamma_low[32], title="Gamma = {}".format(gamma_low_val))
show_plane(c, gamma_high[32], title="Gamma = {}".format(gamma_high_val))

plot_hist(d, data)
plot_hist(e, gamma_low)
plot_hist(f, gamma_high)   


# <markdowncell>
# [Histogram equalization](https://en.wikipedia.org/wiki/Histogram_equalization)
# improves contrast in an image by redistributing pixel intensities. The most
# common pixel intensities are spread out, allowing areas of lower local
# contrast to gain a higher contrast. This may enhance background noise.


# <codecell>

equalized = exposure.equalize_hist(data)

display(equalized)

_, ((a, b), (c, d)) = plt.subplots(nrows=2, ncols=2, figsize=(16, 8))

plot_hist(a, data, title="Original")
plot_hist(b, equalized, title="Histogram equalization")

cdf, bins = exposure.cumulative_distribution(data.ravel())
c.plot(bins, cdf, "r")
c.set_title("Original CDF")

cdf, bins = exposure.cumulative_distribution(equalized.ravel())
d.plot(bins, cdf, "r")
d.set_title("Histogram equalization CDF");   


# <markdowncell>
# Most experimental images are affected by salt and pepper noise. A few bright
# artifacts can decrease the relative intensity of the pixels of interest. A
# simple way to improve contrast is to clip the pixel values on the lowest and
# highest extremes. Clipping the darkest and brightest 0.5% of pixels will
# increase the overall contrast of the image.


# <codecell>

vmin, vmax = stats.scoreatpercentile(data, (0.5, 99.5))

clipped = exposure.rescale_intensity(
    data, 
    in_range=(vmin, vmax), 
    out_range=np.float32
).astype(np.float32)

display(clipped)   


# <codecell>

# Pick your favorite result.
rescaled = clipped   


# <markdowncell>
# ## Edge detection
# 
# [Edge detection](https://en.wikipedia.org/wiki/Edge_detection) highlights
# regions in the image where a sharp change in contrast occurs. The intensity of
# an edge corresponds to the steepness of the transition from one intensity to
# another. A gradual shift from bright to dark intensity results in a dim edge.
# An abrupt shift results in a bright edge.
# 
# The [Sobel operator](https://en.wikipedia.org/wiki/Sobel_operator) is an edge
# detection algorithm which approximates the gradient of the image intensity,
# and is fast to compute. `skimage.filters.sobel` has not been adapted for 3D
# images. It can be applied planewise to approximate a 3D result.


# <codecell>

sobel = np.empty_like(rescaled)

for plane, image in enumerate(rescaled):
    sobel[plane] = filters.sobel(image)
    
display(sobel)   


# <codecell>

_, ((a, b), (c, d)) = plt.subplots(nrows=2, ncols=2, figsize=(16, 4))

show_plane(a, sobel[:, 128, :], title="3D sobel, row = 128")

row_sobel = filters.sobel(rescaled[:, 128, :])
show_plane(b, row_sobel, title="2D sobel, row=128")

show_plane(c, sobel[:, :, 128], title="3D sobel, column = 128")

column_sobel = filters.sobel(rescaled[:, :, 128])
show_plane(d, column_sobel, title="2D sobel, column=128")   


# <markdowncell>
# ## Filters
# 
# In addition to edge detection, `skimage.filters` provides functions for
# filtering and thresholding images.
# 
# [Gaussian filter](https://en.wikipedia.org/wiki/Gaussian_filter) applies a
# Gaussian function to an image, creating a smoothing effect.
# `skimage.filters.gaussian` takes as input `sigma` which can be a scalar or a
# sequence of scalar. This `sigma` determines the standard deviation of the
# Gaussian along each axis. When the resolution in the `plane` dimension is much
# worse than the `row` and `column` dimensions, dividing `base_sigma` by the
# image `spacing` will balance the contribution to the filter along each axis.


# <codecell>

base_sigma = 3.0

sigma = base_sigma / spacing

gaussian = filters.gaussian(rescaled, multichannel=False, sigma=sigma)

display(gaussian)   


# <markdowncell>
# [Median filter](https://en.wikipedia.org/wiki/Median_filter) is a noise
# removal filter. It is particularly effective against salt and pepper noise. An
# additional feature of the median filter is its ability to preserve edges. This
# is helpful in segmentation because the original shape of regions of interest
# will be preserved.
# 
# `skimage.filters.median` does not support three-dimensional images and needs
# to be applied planewise.


# <codecell>

rescaled_uint8 = util.img_as_ubyte(rescaled)

median = np.empty_like(rescaled_uint8)

for plane, image in enumerate(rescaled_uint8):
    median[plane] = filters.median(image)
    
median = util.img_as_float(median)
    
display(median)   


# <markdowncell>
# A [bilateral filter](https://en.wikipedia.org/wiki/Bilateral_filter) is
# another edge-preserving, denoising filter. Each pixel is assigned a weighted
# average based on neighboring pixels. The weight is determined by spatial and
# radiometric similarity (e.g., distance between two colors).
# 
# `skimage.restoration.denoise_bilateral` requires a `multichannel` parameter.
# This determines whether the last axis of the image is to be interpreted as
# multiple channels or another spatial dimension. While the function does not
# yet support 3D data, the `multichannel` parameter will help distinguish
# multichannel 2D data from grayscale 3D data.


# <codecell>

bilateral = np.empty_like(rescaled)

for index, plane in enumerate(rescaled):
    bilateral[index] = restoration.denoise_bilateral(
        plane, 
        multichannel=False
    )

display(bilateral)   


# <codecell>

_, (a, b, c, d) = plt.subplots(nrows=1, ncols=4, figsize=(16, 4))

show_plane(a, rescaled[32], title="Original")
show_plane(b, gaussian[32], title="Gaussian")
show_plane(c, median[32], title="Median")
show_plane(d, bilateral[32], title="Bilateral")   


# <codecell>

denoised = bilateral   


# <markdowncell>
# [Thresholding](https://en.wikipedia.org/wiki/Thresholding_%28image_processing%
# 29) is used to create binary images. A threshold value determines the
# intensity value separating foreground pixels from background pixels. Foregound
# pixels are pixels brighter than the threshold value, background pixels are
# darker. Thresholding is a form of image segmentation.
# 
# Different thresholding algorithms produce different results. [Otsu's
# method](https://en.wikipedia.org/wiki/Otsu%27s_method) and Li's minimum cross
# entropy threshold are two common algorithms. The example below demonstrates
# how a small difference in the threshold value can visibly alter the binarized
# image.


# <codecell>

threshold_li = filters.threshold_li(denoised)
li = denoised >= threshold_li

threshold_otsu = filters.threshold_otsu(denoised)
otsu = denoised >= threshold_otsu

_, (a, b, c) = plt.subplots(nrows=1, ncols=3, figsize=(16, 4))

plot_hist(a, denoised, "Thresholds (Li: red, Otsu: blue)")
a.axvline(threshold_li, c="r")
a.axvline(threshold_otsu, c="b")

show_plane(b, li[32], title="Li's threshold = {:0.3f}".format(threshold_li))
show_plane(c, otsu[32], title="Otsu's threshold = {:0.3f}".format(threshold_otsu))   


# <codecell>

binary = li

display(binary)   


# <markdowncell>
# ## Morphological operations


# <markdowncell>
# [Mathematical
# morphology](https://en.wikipedia.org/wiki/Mathematical_morphology) operations
# and structuring elements are defined in `skimage.morphology`. Structuring
# elements are shapes which define areas over which an operation is applied. The
# response to the filter indicates how well the neighborhood corresponds to the
# structuring element's shape.
# 
# There are a number of two and three dimensional structuring elements defined
# in `skimage.morphology`. Not all 2D structuring element have a 3D counterpart.
# The simplest and most commonly used structuring elements are the `disk`/`ball`
# and `square`/`cube`.


# <codecell>

ball = morphology.ball(radius=5)
print("ball shape: {}".format(ball.shape))

cube = morphology.cube(width=5)
print("cube shape: {}".format(cube.shape))   


# <markdowncell>
# The most basic mathematical morphology operations are `dilation` and
# `erosion`. Dilation enlarges bright regions and shrinks dark regions. Erosion
# shrinks bright regions and enlarges dark regions. Other morphological
# operations are composed of `dilation` and `erosion`.
# 
# The `closing` of an image is defined as a `dilation` followed by an `erosion`.
# Closing can remove small dark spots (i.e. “pepper”) and connect small bright
# cracks. This tends to “close” up (dark) gaps between (bright) features.
# Morphological `opening` on an image is defined as an `erosion` followed by a
# `dilation`. Opening can remove small bright spots (i.e. “salt”) and connect
# small dark cracks. This tends to “open” up (dark) gaps between (bright)
# features.
# 
# These operations in `skimage.morphology` are compatible with 3D images and
# structuring elements. A 2D structuring element cannot be applied to a 3D
# image, nor can a 3D structuring element be applied to a 2D image.
# 
# These four operations (`closing`, `dilation`, `erosion`, `opening`) have
# binary counterparts which are faster to compute than the grayscale algorithms.


# <codecell>

selem = morphology.ball(radius=3)

closing = morphology.closing(rescaled, selem=selem)
dilation = morphology.dilation(rescaled, selem=selem)
erosion = morphology.erosion(rescaled, selem=selem)
opening = morphology.opening(rescaled, selem=selem)

binary_closing = morphology.binary_closing(binary, selem=selem)
binary_dilation = morphology.binary_dilation(binary, selem=selem)
binary_erosion = morphology.binary_erosion(binary, selem=selem)
binary_opening = morphology.binary_opening(binary, selem=selem)

_, ((a, b, c, d), (e, f, g, h)) = plt.subplots(nrows=2, ncols=4, figsize=(16, 8))

show_plane(a, erosion[32], title="Erosion")
show_plane(b, dilation[32], title="Dilation")
show_plane(c, closing[32], title="Closing")
show_plane(d, opening[32], title="Opening")

show_plane(e, binary_erosion[32], title="Binary erosion")
show_plane(f, binary_dilation[32], title="Binary dilation")
show_plane(g, binary_closing[32], title="Binary closing")
show_plane(h, binary_opening[32], title="Binary opening")   


# <markdowncell>
# Morphology operations can be chained together to denoise an image. For
# example, a `closing` applied to an `opening` can remove salt and pepper noise
# from an image.


# <codecell>

binary_equalized = equalized >= filters.threshold_li(equalized)

despeckled1 = morphology.closing(
    morphology.opening(binary_equalized, selem=morphology.ball(1)),
    selem=morphology.ball(1)
)

despeckled3 = morphology.closing(
    morphology.opening(binary_equalized, selem=morphology.ball(3)),
    selem=morphology.ball(3)
)

_, (a, b, c) = plt.subplots(nrows=1, ncols=3, figsize=(16, 4))

show_plane(a, binary_equalized[32], title="Noisy data")
show_plane(b, despeckled1[32], title="Despeckled, r = 1")
show_plane(c, despeckled3[32], title="Despeckled, r = 3")   


# <markdowncell>
# Functions operating on [connected
# components](https://en.wikipedia.org/wiki/Connected_space) can remove small
# undesired elements while preserving larger shapes.
# 
# `skimage.morphology.remove_small_holes` fills holes and
# `skimage.morphology.remove_small_objects` removes bright regions. Both
# functions accept a `min_size` parameter, which is the minimum size (in pixels)
# of accepted holes or objects. The `min_size` can be approximated by a cube.


# <codecell>

width = 20

remove_holes = morphology.remove_small_holes(
    binary, 
    min_size=width ** 3
)

display(remove_holes)   


# <codecell>

width = 20

remove_objects = morphology.remove_small_objects(
    remove_holes, 
    min_size=width ** 3
)

display(remove_objects)   


# <markdowncell>
# ## Segmentation


# <markdowncell>
# [Image segmentation](https://en.wikipedia.org/wiki/Image_segmentation)
# partitions images into regions of interest. Interger labels are assigned to
# each region to distinguish regions of interest.


# <codecell>

# Display label matrices with the background value 0 set to black.
def get_cmap(labels, name="viridis"):
    cmap = cm.get_cmap("viridis")
    masked_labels = np.ma.masked_where(labels == 0, labels)
    cmap.set_bad(color="black")
    
    return masked_labels, cmap   


# <codecell>

labels = measure.label(remove_objects)

masked_labels, cmap = get_cmap(labels)

display(masked_labels, cmap=cmap)   


# <markdowncell>
# Connected components of the binary image are assigned the same label via
# `skimage.measure.label`. Tightly packed cells  connected in the binary image
# are assigned the same label.


# <codecell>

_, (a, b, c) = plt.subplots(nrows=1, ncols=3, figsize=(16, 4))

show_plane(a, rescaled[32, :100, 125:], title="Rescaled")
show_plane(b, masked_labels[32, :100, 125:], cmap=cmap, title="Labels")
show_plane(c, labels[32, :100, 125:] == 8, title="Labels = 8")   


# <markdowncell>
# A better segmentation would assign different labels to disjoint regions in the
# original image.
# 
# [Watershed
# segmentation](https://en.wikipedia.org/wiki/Watershed_%28image_processing%29)
# can distinguish touching objects. Markers are placed at local minima and
# expanded outward until there is a collision with markers from another region.
# The inverse intensity image transforms bright cell regions into basins which
# should be filled.
# 
# In declumping, markers are generated from the distance function. Points
# furthest from an edge have the highest intensity and should be identified as
# markers using `skimage.feature.peak_local_max`. Regions with pinch points
# should be assigned multiple markers.


# <codecell>

distance = ndi.distance_transform_edt(remove_objects)

peak_local_max = feature.peak_local_max(
    distance,
    footprint=np.ones((15, 15, 15), dtype=np.bool),
    indices=False,
    labels=measure.label(remove_objects)
)

markers = measure.label(peak_local_max)

labels = morphology.watershed(
    -rescaled, 
    markers, 
    mask=remove_objects
)

masked_labels, cmap = get_cmap(labels)

display(masked_labels, cmap=cmap)   


# <markdowncell>
# Watershed successfully distinguishes clumped objects in the thresholded image.
# Below are two examples of clumped objects successfully assigned unque labels.
# In the second row of images, the two cells touching the border of the image
# are assigned the same label. It is challenging to distinguish clumped objects
# near the borders of images. In practice, objects touching the border of the
# image are discarded before feature extraction.


# <codecell>

_, ((a, b, c), (d, e, f)) = plt.subplots(nrows=2, ncols=3, figsize=(16, 8))

show_plane(a, masked_labels[32, :100, 125:], cmap=cmap, title="Labels")
show_plane(b, labels[32, :100, 125:] == 20, title="Labels = 20")
show_plane(c, labels[32, :100, 125:] == 21, title="Labels = 21")

show_plane(d, masked_labels[32, 75:175, 125:], cmap=cmap, title="Labels")
show_plane(e, labels[32, 75:175, 125:] == 13, title="Labels = 13")
show_plane(f, labels[32, 75:175, 125:] == 14, title="Labels = 14")   


# <markdowncell>
# The watershed algorithm falsely detected subregions in a few cells. This is
# referred to as oversegmentation.


# <codecell>

_, (a, b, c) = plt.subplots(nrows=1, ncols=3, figsize=(16, 8))

show_plane(a, masked_labels[32, 156:, 20:150], cmap=cmap)
show_plane(b, masked_labels[34, 90:190, 126:], cmap=cmap)
show_plane(c, masked_labels[32, 150:, 118:248], cmap=cmap)   


# <markdowncell>
# Plotting the markers on the distance image reveals the reason for
# oversegmentation. Cells with multiple markers will be assigned multiple
# labels, and oversegmented. It can be observed that cells with a uniformly
# increasing distance map are assigned a single marker near their center. Cells
# with uneven distance maps are assigned multiple markers, indicating the
# presence of multiple local maxima.


# <codecell>

_, axes = plt.subplots(nrows=3, ncols=4, figsize=(16, 12))

vmin = distance.min()
vmax = distance.max()

for index, ax in enumerate(axes.flatten()):
    ax.imshow(
        distance[31 + index],
        cmap="gray",
        vmin=vmin,
        vmax=vmax
    )
    
    peaks = np.nonzero(peak_local_max[31 + index])
    
    ax.plot(peaks[1], peaks[0], "r.")
    ax.set_xticks([])
    ax.set_yticks([])   


# <codecell>

_, ((a, b, c), (d, e, f)) = plt.subplots(nrows=2, ncols=3, figsize=(16, 8))

show_plane(a, remove_objects[10:, 193:253, 74])
show_plane(b, remove_objects[10:, 110:170, 184])
show_plane(c, remove_objects[10:, 170:230, 179])

show_plane(d, distance[10:, 193:253, 74])
show_plane(e, distance[10:, 110:170, 184])
show_plane(f, distance[10:, 170:230, 179])   


# <markdowncell>
# ## Feature extraction


# <markdowncell>
# [Feature extraction](https://en.wikipedia.org/wiki/Feature_extraction) reduces
# data required to describe an image or objects by measuring informative
# features. These include features such as area or volume, bounding boxes, and
# intensity statistics.
# 
# Before measuring objects, it helps to clear objects from the image border.
# Measurements should only be collected for objects entirely contained in the
# image.


# <codecell>

interior_labels = segmentation.clear_border(labels)

masked_labels, cmap = get_cmap(interior_labels)

print("interior labels: {}".format(np.unique(interior_labels)))

display(masked_labels, cmap=cmap)   


# <markdowncell>
# After clearing the border, the object labels are no longer sequentially
# increasing. The labels can be renumbered such that there are no jumps in the
# list of image labels.


# <codecell>

relabeled, _, _ = segmentation.relabel_sequential(interior_labels)

print("relabeled labels: {}".format(np.unique(relabeled)))   


# <markdowncell>
# `skimage.measure.regionprops` automatically measures many labeled image
# features. Optionally, an `intensity_image` can be supplied and intensity
# features are extracted per object. It's good practice to make measurements on
# the original image.
# 
# Not all properties are supported for 3D data. Below are lists of supported and
# unsupported 3D measurements.


# <codecell>

regionprops = measure.regionprops(relabeled, intensity_image=data)

supported = [] 
unsupported = []

for prop in regionprops[0]:
    try:
        regionprops[0][prop]
        supported.append(prop)
    except NotImplementedError:
        unsupported.append(prop)

print("Supported properties:")
print("  " + "\n  ".join(supported))
print()
print("Unsupported properties:")
print("  " + "\n  ".join(unsupported))   


# <markdowncell>
# `skimage.measure.regionprops` ignores the 0 label, which represents the
# background.


# <codecell>

print("measured regions: {}".format([regionprop.label for regionprop in regionprops]))   


# <markdowncell>
# `.prop` or `["prop"]` can be used to access extracted properties.


# <codecell>

volumes = [regionprop.area for regionprop in regionprops]

print("total pixels: {}".format(volumes))   


# <markdowncell>
# Collected measurements can be further reduced by computing per-image
# statistics such as total, minimum, maximum, mean, and standard deviation.


# <codecell>

max_volume = np.max(volumes)
mean_volume = np.mean(volumes)
min_volume = np.min(volumes)
sd_volume = np.std(volumes)
total_volume = np.sum(volumes)

print("Volume statistics")
print("total: {}".format(total_volume))
print("min: {}".format(min_volume))
print("max: {}".format(max_volume))
print("mean: {:0.2f}".format(mean_volume))
print("standard deviation: {:0.2f}".format(sd_volume))   


# <markdowncell>
# Perimeter measurements are not computed for 3D objects. The 3D extension of
# perimeter is surface area. We can measure the surface of an object by
# generating a surface mesh with `skimage.measure.marching_cubes` and computing
# the surface area of the mesh with `skimage.measure.mesh_surface_area`.


# <codecell>

# skimage.measure.marching_cubes expects ordering (row, col, pln)
volume = (relabeled == regionprops[3].label).transpose(1, 2, 0)

verts_px, faces_px, _, _ = measure.marching_cubes(volume, level=0, spacing=(1.0, 1.0, 1.0))
surface_area_pixels = measure.mesh_surface_area(verts_px, faces_px)

verts, faces, _, _ = measure.marching_cubes(volume, level=0, spacing=tuple(spacing))
surface_area_actual = measure.mesh_surface_area(verts, faces)

print("surface area (total pixels): {:0.2f}".format(surface_area_pixels))
print("surface area (actual): {:0.2f}".format(surface_area_actual))   


# <markdowncell>
# The volume can be visualized using the mesh vertexes and faces.


# <codecell>

fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection="3d")

mesh = Poly3DCollection(verts_px[faces_px])
mesh.set_edgecolor("k")
ax.add_collection3d(mesh)

ax.set_xlabel("col")
ax.set_ylabel("row")
ax.set_zlabel("pln")

min_pln, min_row, min_col, max_pln, max_row, max_col = regionprops[3].bbox

ax.set_xlim(min_row, max_row)
ax.set_ylim(min_col, max_col)
ax.set_zlim(min_pln, max_pln)

plt.tight_layout()
plt.show()   


# <markdowncell>
# ## Challenge problems
# 
# Put your 3D image processing skills to the test by working through these
# challenge problems.
# 
# ### Improve the segmentation
# A few objects were oversegmented in the declumping step. Try to improve the
# segmentation and assign each object a single, unique label. You can try:
# 
# 1. generating a smoother image by modifying the `win_size` parameter in
# `skimage.restoration.denoise_bilateral`, or try another filter. Many filters
# are available in `skimage.filters` and `skimage.filters.rank`.
# 1. adjusting the threshold value by trying another threshold algorithm such as
# `skimage.filters.threshold_otsu` or entering one manually.
# 1. generating different markers by changing the size of the footprint passed
# to `skimage.feature.peak_local_max`. Alternatively, try another metric for
# placing markers or limit the planes on which markers can be placed.
# 
# 
# ### Segment cell membranes
# Try segmenting the accompanying membrane channel. In the membrane image, the
# membrane walls are the bright web-like regions. This channel is difficult due
# to a high amount of noise in the image. Additionally, it can be hard to
# determine where the membrane ends in the image (it's not the first and last
# planes).
# 
# Below is a 2D segmentation of the membrane:
# 
# [../_images/membrane_segmentation.png](../_images/membrane_segmentation.png)
# 
# The membrane image can be loaded using
# `skimage.io.imread("../images/cells_membrane.tif")`.
# 
# Hint: there should only be one nucleus per membrane.
