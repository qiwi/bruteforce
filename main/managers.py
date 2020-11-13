from django.core.exceptions import ObjectDoesNotExist
from django.db import models


# This uncertain methods exist because AES always has different strings from output
# For bypass this deplorable fact all hashes need to be decrypted before comparison
class HashQuerySet(models.QuerySet):
    def get(self, *args, **kwargs):
        if kwargs.get("hash"):
            h = kwargs.pop("hash")
            for row in self.all():
                if row.hash == h:
                    kwargs.pop("id")  # get by hash and id both not allowed
                    return super().get(id=row.id, *args, **kwargs)
            raise ObjectDoesNotExist("Hash matching query does not exist.")
        return super().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        if "OR" in args:
            queryset = None
            for k, v in kwargs.items():
                if queryset is None:
                    queryset = self.filter(**{k: v})
                else:
                    queryset |= self.filter(**{k: v})
            hashes_idx = [row.id for row in queryset]
            return super().filter(id__in=hashes_idx)
        elif "password" in kwargs:
            p = kwargs.pop("password")
            hashes_idx = [row.id for row in self.all() if p == row.password]
            return super().filter(id__in=hashes_idx, **kwargs)
        elif "password__contains" in kwargs:
            p = kwargs.pop("password__contains")
            hashes_idx = [row.id for row in self.all() if p in row.password]
            return super().filter(id__in=hashes_idx, **kwargs)
        elif "password__icontains" in kwargs:
            p = kwargs.pop("password__icontains")
            hashes_idx = [
                row.id
                for row in self.all()
                if row._encrypted_password and p.lower() in row.password.lower()
            ]
            return super().filter(id__in=hashes_idx, **kwargs)
        elif "is_hacked" in kwargs:
            is_hacked = kwargs.pop("is_hacked")
            hashes_idx = [
                row.id
                for row in self.all()
                if is_hacked == bool(row._encrypted_password)
            ]
            return super().filter(id__in=hashes_idx, **kwargs)
        elif "hash" in kwargs:
            h = kwargs.pop("hash")
            hashes_idx = [row.id for row in self.all() if h == row.hash]
            return super().filter(id__in=hashes_idx, **kwargs)
        elif "hash__contains" in kwargs:
            h = kwargs.pop("hash__contains")
            hashes_idx = [row.id for row in self.all() if h in row.hash]
            return super().filter(id__in=hashes_idx, **kwargs)
        elif "hash__icontains" in kwargs:
            h = kwargs.pop("hash__icontains")
            hashes_idx = [row.id for row in self.all() if h.lower() in row.hash.lower()]
            return super().filter(id__in=hashes_idx, **kwargs)
        elif "hash__in" in kwargs:
            h_list = kwargs.pop("hash__in")
            hashes_idx = []
            for row in self.all():
                hash_ = row.hash
                for h in h_list:
                    if h in hash_:
                        hashes_idx.append(row.id)
                        break
            return super().filter(id__in=hashes_idx, **kwargs)
        else:
            return super().filter(**kwargs)

    def exclude(self, *args, **kwargs):
        if "hash" in kwargs:
            h = kwargs.pop("hash")
            hashes_idx = [row.id for row in self.all() if h != row.hash]
            return super().filter(id__in=hashes_idx, *args, **kwargs)
        return super().exclude(*args, **kwargs)
