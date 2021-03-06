
# coding: utf-8



# <codecell>

%matplotlib inline
import matplotlib
matplotlib.rcParams['image.cmap'] = 'gray'
matplotlib.rcParams['image.interpolation'] = 'nearest'   


# <markdowncell>
# # RANSAC
# 
# From WikiPedia:
# 
# > Random sample consensus (RANSAC) is an iterative method to estimate
# > parameters of a mathematical model from a set of observed data which
# > contains outliers. Therefore, it also can be interpreted as an
# > outlier detection method.
# 
# [Gallery example](http://scikit-
# image.org/docs/dev/auto_examples/plot_matching.html)


# <codecell>

import numpy as np
from matplotlib import pyplot as plt

from skimage.measure import ransac   


# <markdowncell>
# Let's set up some random data points:


# <codecell>

np.random.seed(seed=1)

# generate coordinates of line
x = np.arange(-200, 200)
y = 0.2 * x + 20
data = np.column_stack([x, y])

# add faulty data
faulty = np.array(30 * [(180., -100)])
faulty += 5 * np.random.normal(size=faulty.shape)
data[:faulty.shape[0]] = faulty

# add gaussian noise to coordinates
noise = np.random.normal(size=data.shape)
data += 0.5 * noise
data[::2] += 5 * noise[::2]
data[::4] += 20 * noise[::4]

plt.plot(data[:, 0], data[:, 1], 'b.');   


# <markdowncell>
# Now, fit a line to the data.  We start with our model:
# 
# $$\mathbf{y} = m \mathbf{x} + c$$
# 
# Or, in matrix notation:
# 
# $$\mathbf{y} = \left[ \begin{array}{c} \vdots \\ \mathbf{x} \\ \vdots
# \end{array}
#                      \ \begin{array}{c} \vdots \\ \mathbf{1} \\ \vdots
# \end{array} \right]
#                      \left[ \begin{array}{c} m \\ c \end{array} \right]
#                      = X \mathbf{p}$$
# 
# Since we have an over-determined system, we use least squares to solve:


# <codecell>

x = data[:, 0]
y = data[:, 1]

X = np.column_stack((x, np.ones_like(x)))

p, _, _, _ = np.linalg.lstsq(X, y)
p   


# <markdowncell>
# With those parameters in hand, let's plot the resulting line:


# <codecell>

m, c = p
plt.plot(x, y, 'b.')

xx = np.arange(-250, 250)
plt.plot(xx, m * xx + c, 'r-');   


# <markdowncell>
# Scikit-image provides an N-dimensional LineModel object that encapsulates the
# above:


# <codecell>

from skimage.measure import ransac, LineModelND

model = LineModelND()
model.estimate(data)
model.params   


# <markdowncell>
# Instead of ``m`` and ``c``, it parameterizes the line by ``origin``
# and ``direction`` --- much safer when dealing with vertical lines,
# e.g.!


# <codecell>

origin, direction = model.params
plt.plot(x, y, 'b.')
plt.plot(xx, model.predict_y(xx), 'r-');   


# <markdowncell>
# Now, we robustly fit the line using inlier data selecte with the RANSAC
# algorithm:


# <codecell>

model_robust, inliers = ransac(data, LineModelND, min_samples=2,
                               residual_threshold=10, max_trials=1000)
outliers = (inliers == False)

yy = model_robust.predict_y(xx)

fig, ax = plt.subplots()

ax.plot(data[inliers, 0], data[inliers, 1], '.b', alpha=0.6, label='Inlier data')
ax.plot(data[outliers, 0], data[outliers, 1], '.r', alpha=0.6, label='Outlier data')
ax.plot(xx, yy, '-b', label='Robust line model')

plt.legend(loc='lower left')
plt.show()   


# <markdowncell>
# ## Exercise: Going interplanetary
# 
# The sun is one of the most spherical objects in our solar system.
# According to an [article in Scientific
# American](http://www.scientificamerican.com/gallery/well-rounded-sun-stays-
# nearly-spherical-even-when-it-freaks-out/):
# 
# > Earth's closest star is one of the roundest objects humans have
# > measured. If you shrank the sun down to beach ball size, the
# > difference between its north-south and the east-west diameters would
# > be thinner than the width of a human hair, says Jeffery Kuhn, a
# > physicist and solar researcher at the University of Hawaii at
# > Manoa. "Not only is it very round, but it's too round," he adds. The
# > sun is more spherical and more invariable than theories predict.
# 
# If the sun is spherical, we should be able to fit a circle to a 2D
# slice of it!  Your task is to do just that, using RANSAC and scikit-image's
# CircleModel.
# 
# Let's start by loading an example image:


# <codecell>

from skimage import io

image = io.imread('../images/superprom_prev.jpg')

f, ax = plt.subplots(figsize=(8, 8))
ax.imshow(image);   


# <markdowncell>
# In this specific image, we got a bit more than we bargained for in the
# form of magnificently large solar flares.  Let's see if some *canny
# edge detection* will help isolate the sun's boundaries.


# <codecell>

from skimage import feature, color

# Step 1: convert the image from color to gray, using `color.rgb2gray`

...

# Step 2: do edge detection on the image, using `feature.canny`.  Play around with the `sigma`
# parameter until you get a reasonable set of edges.

f, ax = plt.subplots(figsize=(10, 10))
ax.imshow(my_result, cmap='gray')   


# <markdowncell>
# The edges look good, but there's a lot going on inside the sun.  We
# use RANSAC to fit a robust circle model.


# <codecell>

from skimage.measure import CircleModel

points = ...    # Let points be an array with coordinate positions of edge pixels found above, shape (N, 2)

model_robust, inliers = ransac(...)   


# <markdowncell>
# The parameters of the circle are center x, y and radius:


# <codecell>

model_robust.params   


# <markdowncell>
# Let's visualize the results, drawing a circle on the sun, and also
# highlighting inlier vs outlier edge pixels:


# <codecell>

from skimage import draw

cy, cx, r = model_robust.params

f, (ax0, ax1) = plt.subplots(1, 2, figsize=(15, 8))

ax0.imshow(image)
ax1.imshow(image)

ax1.plot(points[inliers, 1], points[inliers, 0], 'b.', markersize=1)
ax1.plot(points[~inliers, 1], points[~inliers, 0], 'g.', markersize=1)
ax1.axis('image')

circle = plt.Circle((cx, cy), radius=r, facecolor='none', linewidth=2)
ax0.add_patch(circle);   


# <markdowncell>
# ## Exercise: CardShark
# 
# Your small start-up, CardShark, that you run from your garage over nights and
# evenings, takes photos of credit cards and turns them into machine
# readable information.
# 
# The first step is to identify where in a photo the credit card is
# located.
# 
# 1. Load the photo `../images/credit_card.jpg`
# 2. Using RANSAC and LineModelND shown above, find the first most
#    prominent edge of the card
# 3. Remove the edge points belonging to the most prominent edge, and
#    repeat the process to find the second, third, and fourth


# <codecell>

f, ax = plt.subplots()

image = io.imread('../images/credit_card.jpg')
ax.imshow(image);   
