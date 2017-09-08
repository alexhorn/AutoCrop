import argparse
import cv2
import logging
import math
import numpy as np
from os import path
from shapely import affinity
from shapely.geometry import Polygon
from squares import find_squares, angle_cos
from wand.display import display
from wand.image import Image

ERR_FILE_READ = 'Could not read %s'

def remove_squares_touching_border(squares, size, border):
    """Remove squares too close to the image border."""

    square_doesnt_touch_border = lambda square: not any(
        a < border[0] * size[0]
        or a > (1 - border[0]) * size[0]
        or b < border[1] * size[1]
        or b > (1 - border[1]) * size[1]
        for a, b in square
    )
    return filter(square_doesnt_touch_border, squares)

def squarest_contour(squares):
    """Find the square whose corners are closest to 90°."""

    return min(squares, key=lambda cnt: np.max([angle_cos(cnt[i], cnt[(i+1) % 4], cnt[(i+2) % 4]) for i in range(4)]))

def remove_overlapping_squares(squares):
    """Get the best square out of every group of intersecting squares."""

    polys = [Polygon(square) for square in squares]
    best_squares = []
    for p1 in polys:
        best = squarest_contour(np.array(list(p2.exterior.coords)) for p2 in polys if p1.intersects(p2))
        if not any(np.array_equiv(best, p2) for p2 in best_squares):
            best_squares.append(best)
    return best_squares

def remove_duplicate_points(points):
    """Remove duplicate numpy arrays. (similar to np.unique but without the sorting)"""

    unique = []
    for elem in points:
        if not any(np.array_equal(elem, other) for other in unique):
            unique.append(elem)
    return np.array(unique)

def get_angle(p1, p2):
    """Get the angle between two points."""

    return math.atan2(p2[1] - p1[1], p2[0] - p1[0])

def get_tilt(square):
    """Get average tilt of the squares edges."""

    assert len(square) == 4
    return np.mean([
        get_angle(square[0], square[1]),
        -0.5*np.pi + get_angle(square[1], square[2]),
        np.pi + get_angle(square[2], square[3]),
        0.5*np.pi + get_angle(square[3], square[0])
    ])

def find_photos(img):
    """Find photos in a scan."""

    # find squares
    logging.debug('Searching squares')
    squares = find_squares(img)

    # remove squares too close to the border
    logging.debug('Removing squares too close to the border')
    height, width = img.shape[:2]
    squares = remove_squares_touching_border(squares, (width, height), (0.02, 0.02))

    # remove overlapping squares
    logging.debug('Removing overlapping squares')
    squares = remove_overlapping_squares(squares)

    # remove duplicate points
    logging.debug('Removing duplicate points')
    squares = map(remove_duplicate_points, squares)

    return squares

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(description='Crops out photos from a scan.')
parser.add_argument('--input', type=str)
parser.add_argument('--quality', type=int)
parser.add_argument('--force', action='store_true')
args = parser.parse_args()

# read image
img = cv2.imread(args.input, cv2.IMREAD_COLOR)
assert img is not None, ERR_FILE_READ % args.input

# find photos
squares = find_photos(img)

#cv2.drawContours( img, squares, -1, (0, 255, 0), 1 )
#cv2.imshow('contours', img)
#cv2.waitKey(0)

root, ext = path.splitext(args.input)
for square_idx, square in enumerate(squares):
    output = '%s.%d%s' % (root, square_idx, ext)
    with Image(filename=args.input) as image:
        # get square angle
        correction_angle = 90 - math.degrees(get_tilt(square))

        # rotate polygon
        logging.debug('Rotating polygon by %f°' % correction_angle)
        height, width = img.shape[:2]
        corrected_polygon = affinity.rotate(Polygon(square), correction_angle, origin=(width / 2, height / 2))

        # rotate image
        logging.debug('Rotating image')
        width_before, height_before = image.size
        image.rotate(correction_angle)
        width_after, height_after = image.size

        # offset polygon to match image
        logging.debug('Moving polygon')
        offset_x = (width_after - width_before) / 2
        offset_y = (height_after - height_before) / 2
        corrected_polygon = affinity.translate(corrected_polygon, offset_x, offset_y)

        # crop image
        logging.debug('Cropping image')
        image.crop(*map(round, corrected_polygon.bounds))

        # save image
        logging.info('Saving %s' % output)
        assert args.force or not path.isfile(output), 'File exists already'
        if args.quality:
            image.compression_quality=args.quality
        image.save(filename=output)
