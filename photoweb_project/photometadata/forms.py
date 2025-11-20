from django import forms
from .models import PhotoMetadata

class PhotoMetaForm(forms.Form):
    """
    Форма для ввода метаданных о фото.
    Поля: обязательные и необязательные.
    """
    title = forms.CharField(max_length=200, label="Название")
    photographer = forms.CharField(max_length=200, label="Фотограф")
    date_taken = forms.DateField(
        input_formats=['%Y-%m-%d'],
        label="Дата съемки (YYYY-MM-DD)",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    url = forms.URLField(label="URL изображения")
    description = forms.CharField(widget=forms.Textarea, required=True)
    location = forms.CharField(max_length=200, required=True)
    tags = forms.CharField(required=True, help_text="Через запятую")
    width = forms.IntegerField(required=True, min_value=0)
    height = forms.IntegerField(required=True, min_value=0)
    camera = forms.CharField(max_length=200, required=True)
    license = forms.CharField(max_length=200, required=True)

class UploadFileForm(forms.Form):
    """
    Простая форма загрузки файла.
    Мы не доверяем имени файла, только содержимому.
    """
    file = forms.FileField(label="Файл JSON")

class PhotoMetaModelForm(forms.ModelForm):
    class Meta:
        model = PhotoMetadata
        fields = [
            'title','photographer','date_taken','url','description','location',
            'tags','width','height','camera','license'
        ]
        widgets = {
            'date_taken': forms.DateInput(attrs={'type':'date'}),
        }
