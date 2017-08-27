from PIL import Image
from PIL.ExifTags import TAGS


def get_exif(fn):
    ret = {}
    i = Image.open(fn)
    info = i._getexif()
    print(i)
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        ret[decoded] = value
    return ret
get_exif('/Users/manthansharma/Projects/PycharmProjects/doselect/images/1.jpg')