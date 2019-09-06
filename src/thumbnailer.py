'''
https://gist.github.com/olooney/1601455

PIL's Image.thumbnail() returns an image that fits inside of a given size (preserving aspect ratios)
but the size of the actual image will vary and is certainly not guaranteed to be the requested size.
This is often inconvenient since the size of the returned thumbnail cannot be predicted. The django-thumbs
library solves this for square thumbnails by cropping the image to a square and then resizing it. However,
this only works for exact squares.

This function generalizes that approach to work for thumbnails of any aspect ratio. The returned thumbnail
is always exactly the requested size, and edges (left/right or top/bottom) are cropped off to adjust to
make sure the thumbnail will be the right size without distorting the image.
'''

# TODO: this is only used for the Image.ANTIALIAS constant. seems kind of trivial...
from PIL import Image

def flat( *nums ):
    'Build a tuple of ints from float or integer arguments. Useful because PIL crop and resize require integer points.'
    
    return tuple( int(round(n)) for n in nums )

class Size(object):
    def __init__(self, pair):
        self.width = float(pair[0])
        self.height = float(pair[1])

    @property
    def aspect_ratio(self):
        return self.width / self.height

    @property
    def size(self):
        return flat(self.width, self.height)

def cropped_thumbnail(img, size):
    '''
    Builds a thumbnail by cropping out a maximal region from the center of the original with
    the same aspect ratio as the target size, and then resizing. The result is a thumbnail which is
    always EXACTLY the requested size and with no aspect ratio distortion (although two edges, either
    top/bottom or left/right depending whether the image is too tall or too wide, may be trimmed off.)
    '''
    
    original = Size(img.size)
    target = Size(size)

    if target.aspect_ratio > original.aspect_ratio:
        # image is too tall: take some off the top and bottom
        scale_factor = target.width / original.width
        crop_size = Size( (original.width, target.height / scale_factor) )
        top_cut_line = (original.height - crop_size.height) / 2
        img = img.crop( flat(0, top_cut_line, crop_size.width, top_cut_line + crop_size.height) )
    elif target.aspect_ratio < original.aspect_ratio:
        # image is too wide: take some off the sides
        scale_factor = target.height / original.height
        crop_size = Size( (target.width/scale_factor, original.height) )
        side_cut_line = (original.width - crop_size.width) / 2
        img = img.crop( flat(side_cut_line, 0,  side_cut_line + crop_size.width, crop_size.height) )
        
    return img.resize(target.size, Image.ANTIALIAS)
