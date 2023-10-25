from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage
from django.core.files.storage import default_storage
from django.http import HttpResponse

#minio supp func
def delete_image_from_s3(image_path):
    if image_path:
        storage = S3Boto3Storage()
        storage.delete(image_path)

def upload_image_to_s3(image_data, object_name, content_type):
    storage = S3Boto3Storage()
    image_file = ContentFile(image_data)
    image_file.name = object_name
    storage.save(object_name, image_file)


def get_image_from_s3(request, object_name):
    storage = S3Boto3Storage()
    try:
        image = storage.open(object_name)
        image_data = image.read()
        return image_data
    except Exception as e:
        return None