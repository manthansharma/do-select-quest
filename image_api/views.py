import fnmatch
import os
import re
import uuid

from PIL import Image
from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

EXTENSION = ['.jpeg', '.jpg', '.png', '.gif']
COMPRESSION_EXTENSION = ['.jpeg', '.jpg', '.png']


def authenticate(access_key):
    try:
        access_key = uuid.UUID(access_key)
        if os.path.isdir("{}/{}/".format(settings.IMAGE_ROOT,
                                         access_key.int)):
            return access_key
    except ValueError:
        return None
    except TypeError:
        return None


def save_image(image, path, extension):
    with Image.open(image) as pil_image:
        base_height = 1024
        pil_image_size = pil_image.size

        if extension in COMPRESSION_EXTENSION:
            if pil_image_size[0] > 1536:
                hpercent = (base_height / float(pil_image_size[0]))
                wsize = int((float(pil_image_size[1]) * float(hpercent)))
                pil_image = pil_image.resize((base_height, wsize),
                                             Image.ANTIALIAS)

            pil_image.save(path, quality=75, optimize=True)
        else:
            with open(path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
    return pil_image_size


class ImageList(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        api_key = request.GET.get('api_key', default=None)
        access_key = authenticate(api_key)

        if access_key is None:
            return JsonResponse({
                "error": "Not Authorised"
            }, status=401)

        kwargs["access_key"] = access_key

        return super(ImageList, self).dispatch(request, *args, **kwargs)

    def get(self, request, access_key):
        response_data = {
            "images": []
        }

        for image in os.listdir("{}/{}".format(settings.IMAGE_ROOT,
                                               access_key.int)):
            if re.match(r'index_\d+$', image):
                pass
            else:
                image_id = image.split('_')[0]

                response_data["images"].append({
                    "image_id": image_id,
                    "url": request.build_absolute_uri(
                        "{}/?api_key={}".format(image_id, access_key.hex)),
                    "image_link": request.build_absolute_uri(
                        "//{}{}/{}".format(settings.STATIC_URL,
                                           access_key.int, image))
                })
            response_data["total"] = response_data["images"].__len__()
        return JsonResponse(response_data)

    def post(self, request, access_key):
        image = request.FILES.get('image', default=None)

        if image is None:
            return JsonResponse({
                "image": "This field is required with attached content be "
                         "image files"
            }, status=400)
        extension = os.path.splitext(image.name)[1].lower()
        if extension not in EXTENSION:
            return JsonResponse({
                "image": "Image format is not supported",
                "supported_format": EXTENSION
            }, status=400)

        filenum = fnmatch.filter(os.listdir("{}/{}".format(
            settings.IMAGE_ROOT, access_key.int)
        ), 'index_*')[0].split('_')[1]

        os.rename(
            "{}/{}/index_{}".format(settings.IMAGE_ROOT, access_key.int,
                                    filenum),
            "{}/{}/index_{}".format(settings.IMAGE_ROOT, access_key.int,
                                    int(filenum) + 1))

        image_name = "{}_{}{}".format(filenum, uuid.uuid4().hex,
                                      extension)
        image_path = "{}/{}/{}".format(
            settings.IMAGE_ROOT, access_key.int, image_name)

        pil_image_size = save_image(image, image_path, extension)

        fs = FileSystemStorage()

        return JsonResponse({
            "image_id": filenum,
            "url": request.build_absolute_uri(
                "{}/?api_key={}".format(filenum, access_key.hex)),
            "image_link": request.build_absolute_uri(
                "//{}{}/{}".format(settings.STATIC_URL,
                                   access_key.int, image_name)),
            "size": pil_image_size,
            "created_time": fs.get_created_time(image_path),
        }, status=201)


class ImageDetail(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        api_key = request.GET.get('api_key', default=None)
        access_key = authenticate(api_key)

        if access_key is None:
            return JsonResponse({
                "error": "Not Authorised"
            }, status=401)

        kwargs["access_key"] = access_key

        try:
            filename = fnmatch.filter(os.listdir("{}/{}".format(
                settings.IMAGE_ROOT, access_key.int)
            ), '{}_*'.format(kwargs["pk"]))[0]

            kwargs["filename"] = filename
        except IndexError:
            return JsonResponse({
                "error": "Not Found"
            }, status=404)

        return super(ImageDetail, self).dispatch(request, *args, **kwargs)

    def get(self, request, pk, access_key, filename):
        uploaded_image_url = "{}/{}/{}".format(settings.IMAGE_ROOT,
                                               access_key.int, filename)

        with Image.open(uploaded_image_url) as pil_image:
            pil_image_size = pil_image.size

        fs = FileSystemStorage()
        return JsonResponse({
            "image_id": pk,
            "url": request.build_absolute_uri(),
            "image_link": request.build_absolute_uri(
                "//{}{}/{}".format(settings.STATIC_URL,
                                   access_key.int, filename)),
            "size": pil_image_size,
            "created_time": fs.get_created_time(uploaded_image_url),
        }, status=200)

    def post(self, request, pk, access_key, filename):
        image = request.FILES.get('image', default=None)

        if image is None:
            return JsonResponse({
                "image": "This field is required with attached content be "
                         "image files"
            }, status=400)
        extension = os.path.splitext(image.name)[1].lower()
        if extension not in EXTENSION:
            return JsonResponse({
                "image": "Image format is not supported",
                "supported_format": EXTENSION
            }, status=400)

        old_image_url = "{}/{}/{}".format(settings.IMAGE_ROOT,
                                          access_key.int, filename)
        os.remove(old_image_url)

        if image is None:
            return JsonResponse({
                "image": "This field is required with attached content be "
                         "image files"
            }, status=400)
        image_name = "{}_{}{}".format(pk, uuid.uuid4().hex,
                                      extension)
        image_path = "{}/{}/{}".format(
            settings.IMAGE_ROOT, access_key.int, image_name

        )

        pil_image_size = save_image(image, image_path, extension)

        fs = FileSystemStorage()
        return JsonResponse({
            "image_id": pk,
            "url": request.build_absolute_uri(
                "../{}/?api_key={}".format(pk, access_key.hex)),
            "image_link": request.build_absolute_uri(
                "//{}{}/{}".format(settings.STATIC_URL,
                                   access_key.int, image_name)),
            "size": pil_image_size,
            "created_time": fs.get_created_time(image_path),
        }, status=200)

    def delete(self, request, pk, access_key, filename):
        image_url = "{}/{}/{}".format(settings.IMAGE_ROOT,
                                      access_key.int, filename)
        os.remove(image_url)

        return JsonResponse(data={}, status=204)


@require_http_methods(["GET"])
def generate_auth_token(request):
    token = uuid.uuid1()
    os.makedirs("{}/{}/".format(settings.IMAGE_ROOT, token.int))
    open("{}/{}/index_0".format(settings.IMAGE_ROOT, token.int), 'w').close()
    return JsonResponse({
        'token': token.hex,
        'image_dir': "./images/{}/".format(token.int)
    })


@require_http_methods(["GET"])
def re_generate_auth_token(request):
    api_key = request.GET.get('api_key', default=None)
    access_key = authenticate(api_key)

    if access_key is None:
        return JsonResponse({
            "error": "Not Authorised"
        }, status=401)
    new_token = uuid.uuid1()
    os.rename("{}/{}/".format(settings.IMAGE_ROOT, access_key.int),
              "{}/{}/".format(settings.IMAGE_ROOT, new_token.int))
    return JsonResponse({
        'token': new_token.hex,
        'image_dir': "./images/{}/".format(new_token.int)
    })
