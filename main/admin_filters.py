from django.utils.translation import ugettext_lazy as _
from django.contrib import admin


class HashFilter(admin.SimpleListFilter):
    title = _("cracked")
    parameter_name = "cracked"

    def lookups(self, request, model_admin):
        return (1, _("Yes")), (0, _("No"))

    def queryset(self, request, queryset):
        return (
            queryset.filter(_encrypted_password__isnull=not int(self.value()))
            if self.value()
            else queryset
        )
