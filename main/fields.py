from django.forms.fields import Select
from django import forms


class DbTypeChoiceWidget(Select):
    @property
    def choices(self):
        return ("postgres", "postgres"), ("oracle", "oracle"), ("mssql", "mssql")

    @choices.setter
    def choices(self, _):
        pass


class DbTypeChoiceField(forms.ChoiceField):
    widget = DbTypeChoiceWidget

    def valid_value(self, value):
        return True


class SourceChoiceWidget(Select):
    @property
    def choices(self):
        return (("inventory", "inventory"),)

    @choices.setter
    def choices(self, _):
        pass


class SourceChoiceField(forms.ChoiceField):
    widget = SourceChoiceWidget

    def valid_value(self, value):
        return True
