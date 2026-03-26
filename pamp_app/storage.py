from urllib.parse import urljoin

from django.conf import settings
from storages.backends.s3 import S3Storage


class S3MediaStorage(S3Storage):
    default_acl = None
    file_overwrite = False
    location = 'media'

    def url(self, name: str, parameters=None, expire=None, http_method=None) -> str:
        media_url = getattr(settings, 'MEDIA_URL', '')
        if media_url.startswith(('http://', 'https://')) and not getattr(settings, 'AWS_QUERYSTRING_AUTH', True):
            base_url = media_url if media_url.endswith('/') else f'{media_url}/'
            relative_name = name.lstrip('/')
            location_prefix = f'{self.location.strip("/")}/' if self.location else ''
            if location_prefix and relative_name.startswith(location_prefix):
                relative_name = relative_name[len(location_prefix):]
            return urljoin(base_url, relative_name)
        return super().url(name, parameters=parameters, expire=expire, http_method=http_method)


class CephMediaStorage(S3MediaStorage):
    pass
