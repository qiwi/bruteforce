from django_celery_beat.admin import PeriodicTaskForm, TaskChoiceField, CrontabSchedule
from django.utils.translation import ugettext_lazy as _
from main.fields import SourceChoiceField, DbTypeChoiceField
from main.models import BruteConfig, Dictionary, Database
from django import forms
from typing import Any
import json


class BasePeriodicTaskForm(PeriodicTaskForm):
    def __init__(self, *args: list, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.fields["name"].help_text = "If you leave Name empty it will be generated"
        self.fields["regtask"].help_text = "Do not change this value"
        if kwargs.get("instance"):
            for key, value in json.loads(kwargs["instance"].kwargs).items():
                try:
                    self.fields[key].initial = value
                except Exception as err:
                    print(err)

    name = forms.CharField(label=_("Name"), required=False)
    regtask = TaskChoiceField(label=_("Task (registered)"), required=True)
    enabled = forms.CheckboxInput()
    database = forms.ModelChoiceField(queryset=Database.objects.all().order_by("host"))

    def save(self, commit: bool = True) -> object:
        data = self.data.dict()
        data.pop("csrfmiddlewaretoken")
        data["task"] = data.pop("regtask") or data.pop("task")
        if data.get("name", "").strip():
            data["name"] = data.pop("name").strip()
        else:
            db = Database.objects.get(id=data.get("database"))
            s = "d" if "dictionary" in data else "b"
            i = (
                data.get("dictionary")
                if "dictionary" in data
                else data.get("bruteforce_config")
            )
            self.instance.name = f"{db.host} {s}-{i}"
        self.instance.kwargs = json.dumps(
            {k: data[k] for k in self.fields if k in data}
        )
        self.instance.task = data["task"]
        return super().save(commit=commit)


class DictionaryPeriodicTaskForm(BasePeriodicTaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["regtask"].initial = "Dictionary"

    dictionary = forms.ModelChoiceField(
        queryset=Dictionary.objects.all(), label=_("Dictionary"), required=True
    )


class BruteforcePeriodicTaskForm(BasePeriodicTaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["regtask"].initial = "Bruteforce"

    bruteforce_config = forms.ModelChoiceField(
        queryset=BruteConfig.objects.all(), label=_("Config"), required=True
    )


class DatabaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get("instance"):
            self.initial["ip"] = (
                ",".join(self.initial["ip"]) if self.initial["ip"] else ""
            )
        self.fields["ip"].help_text = "Comma separated value"

    host = forms.CharField(max_length=256)
    ip = forms.CharField(label=_("IP list"), required=False)
    port = forms.IntegerField(required=False)
    db_type = DbTypeChoiceField()

    def clean(self):
        data = self.cleaned_data
        data["ip"] = data["ip"].split(",") if data.get("ip", None) else []
        return data
