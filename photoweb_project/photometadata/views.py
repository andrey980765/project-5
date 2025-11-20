import os
import json
import uuid
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.db import models
from .forms import PhotoMetaForm, UploadFileForm, PhotoMetaModelForm
from .models import PhotoMetadata

# Папка для JSON файлов (media/json)
JSON_DIR = os.path.join(settings.MEDIA_ROOT, 'json')
os.makedirs(JSON_DIR, exist_ok=True)


# --------------------
# Валидация JSON + проверка на дубликат (по всем полям)
# --------------------
def validate_json_data(data_list):
    """
    Проверяет каждую запись списка data_list на наличие всех полей и корректность типов/значений.
    Возвращает (valid_data, errors) — valid_data содержит только корректные записи.
    """
    required_fields = [
        "title", "photographer", "date_taken", "description", "location",
        "tags", "width", "height", "camera", "license", "url"
    ]
    valid_data = []
    errors = []

    for i, record in enumerate(data_list, start=1):
        # Проверка наличия полей
        missing = [f for f in required_fields if f not in record]
        if missing:
            errors.append(f"Запись {i}: отсутствуют поля {', '.join(missing)}.")
            continue

        # Проверка строковых полей
        for field in ["title", "photographer", "description", "location", "camera", "license", "url"]:
            if not isinstance(record.get(field), str) or not record.get(field).strip():
                errors.append(f"Запись {i}: поле '{field}' пустое или не является строкой.")

        # Теги: допускаем пустую строку, но тип должен быть string
        if not isinstance(record.get("tags"), str):
            errors.append(f"Запись {i}: поле 'tags' должно быть строкой (CSV).")

        # Размеры: положительные целые
        try:
            w = int(record.get("width"))
            h = int(record.get("height"))
            if w <= 0 or h <= 0:
                errors.append(f"Запись {i}: width и height должны быть > 0.")
        except Exception:
            errors.append(f"Запись {i}: некорректные значения width/height.")

        # Дата: ISO YYYY-MM-DD
        try:
            date.fromisoformat(str(record.get("date_taken")))
        except Exception:
            errors.append(f"Запись {i}: поле 'date_taken' должно быть в формате YYYY-MM-DD.")

        # Если для данной записи нет ошибок — добавляем в valid_data
        if not any(err for err in errors if f"Запись {i}:" in err):
            # Приводим width/height к int и date к строке ISO (на всякий случай)
            record['width'] = int(record['width'])
            record['height'] = int(record['height'])
            record['date_taken'] = str(record['date_taken'])
            valid_data.append(record)

    return valid_data, errors


def is_duplicate(existing_data, new_record):
    """
    Проверка на дубль: сравниваем все значимые поля строго (строки приведём к lower/strip).
    existing_data: список dict (из файла) или queryset -> приводим к list(dict)
    new_record: dict
    """
    # Приводим существующие записи к унифицированной форме (dict-строки)
    norm_new = {
        'title': str(new_record.get('title', '')).strip().lower(),
        'photographer': str(new_record.get('photographer', '')).strip().lower(),
        'date_taken': str(new_record.get('date_taken')),
        'description': str(new_record.get('description', '')).strip().lower(),
        'location': str(new_record.get('location', '')).strip().lower(),
        'camera': str(new_record.get('camera', '')).strip().lower(),
        'license': str(new_record.get('license', '')).strip().lower(),
        'width': str(new_record.get('width')),
        'height': str(new_record.get('height')),
        'url': str(new_record.get('url', '')).strip().lower(),
        'tags': str(new_record.get('tags', '')).strip().lower(),
    }

    for item in existing_data:
        # item может быть model instance (PhotoMetadata) или dict
        if hasattr(item, 'title'):  # model instance
            norm_item = {
                'title': (item.title or '').strip().lower(),
                'photographer': (item.photographer or '').strip().lower(),
                'date_taken': str(item.date_taken),
                'description': (item.description or '').strip().lower(),
                'location': (item.location or '').strip().lower(),
                'camera': (item.camera or '').strip().lower(),
                'license': (item.license or '').strip().lower(),
                'width': str(item.width),
                'height': str(item.height),
                'url': (item.url or '').strip().lower(),
                'tags': (item.tags or '').strip().lower(),
            }
        else:  # dict from json file
            norm_item = {
                'title': str(item.get('title', '')).strip().lower(),
                'photographer': str(item.get('photographer', '')).strip().lower(),
                'date_taken': str(item.get('date_taken')),
                'description': str(item.get('description', '')).strip().lower(),
                'location': str(item.get('location', '')).strip().lower(),
                'camera': str(item.get('camera', '')).strip().lower(),
                'license': str(item.get('license', '')).strip().lower(),
                'width': str(item.get('width')),
                'height': str(item.get('height')),
                'url': str(item.get('url', '')).strip().lower(),
                'tags': str(item.get('tags', '')).strip().lower(),
            }

        if all(norm_item[k] == norm_new[k] for k in norm_new):
            return True
    return False


# --------------------
# Главная страница: форма добавления и загрузки файла
# --------------------
def index(request):
    """
    Показывает форму добавления (ручной ввод) и форму загрузки JSON.
    Кнопки сохранения: "Сохранить в JSON" -> в файл; "Сохранить в БД" -> в базу.
    """
    form = PhotoMetaForm()
    upload_form = UploadFileForm()
    db_form = PhotoMetaModelForm()

    if request.method == 'POST':
        # Обработка ручной формы: кнопки имеют name="save_metadata" и value="file" или "db"
        if 'save_metadata' in request.POST:
            target = request.POST.get('save_metadata')  # 'file' или 'db'
            form = PhotoMetaForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                # дата -> iso
                if isinstance(data.get("date_taken"), date):
                    data['date_taken'] = data['date_taken'].isoformat()

                if target == 'db':
                    # сохраняем в БД, предварительно проверив на дубликат
                    model_form = PhotoMetaModelForm(data)
                    if model_form.is_valid():
                        qs = PhotoMetadata.objects.filter(
                            title__iexact=model_form.cleaned_data['title'].strip(),
                            photographer__iexact=model_form.cleaned_data['photographer'].strip(),
                            date_taken=model_form.cleaned_data['date_taken']
                        )
                        if is_duplicate(qs, model_form.cleaned_data):
                            messages.warning(request, "Такая запись уже есть в базе — дубликат не добавлен.")
                        else:
                            model_form.save()
                            messages.success(request, "Данные успешно сохранены в базе.")
                    else:
                        messages.error(request, "Ошибка в данных формы для БД.")
                else:
                    # сохраняем в JSON (в первый найденный файл или создаём новый)
                    existing_files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
                    if existing_files:
                        json_path = os.path.join(JSON_DIR, existing_files[0])
                        try:
                            with open(json_path, 'r', encoding='utf-8') as fh:
                                existing_data = json.load(fh)
                                if not isinstance(existing_data, list):
                                    existing_data = [existing_data]
                        except json.JSONDecodeError:
                            existing_data = []

                        if is_duplicate(existing_data, data):
                            messages.warning(request, "Такая запись уже есть в файле — дубликат не добавлен.")
                        else:
                            existing_data.append(data)
                            with open(json_path, 'w', encoding='utf-8') as fh:
                                json.dump(existing_data, fh, ensure_ascii=False, indent=4)
                            messages.success(request, f"Данные добавлены в файл {existing_files[0]}")
                    else:
                        filename = f"{uuid.uuid4().hex}.json"
                        json_path = os.path.join(JSON_DIR, filename)
                        with open(json_path, 'w', encoding='utf-8') as fh:
                            json.dump([data], fh, ensure_ascii=False, indent=4)
                        messages.success(request, f"Создан новый файл {filename}")

                return redirect('photometadata:index')
            else:
                messages.error(request, "Проверьте правильность заполнения формы.")

        # Обработка загрузки JSON-файла
        if 'upload_file' in request.POST:
            upload_form = UploadFileForm(request.POST, request.FILES)
            if upload_form.is_valid():
                file = upload_form.cleaned_data['file']
                try:
                    new_data = json.load(file)
                    if not isinstance(new_data, list):
                        new_data = [new_data]
                except json.JSONDecodeError:
                    messages.error(request, "Ошибка: некорректный JSON-файл.")
                    return redirect('photometadata:index')

                # Валидация загруженных записей
                new_data, validation_errors = validate_json_data(new_data)
                if validation_errors:
                    for err in validation_errors:
                        messages.error(request, err)
                    return redirect('photometadata:index')

                # Сохраняем все валидные записи в единый JSON-файл (первый найденный) или создаём новый
                existing_files = [f for f in os.listdir(JSON_DIR) if f.endswith('.json')]
                if existing_files:
                    json_path = os.path.join(JSON_DIR, existing_files[0])
                    try:
                        with open(json_path, 'r', encoding='utf-8') as fh:
                            existing_data = json.load(fh)
                            if not isinstance(existing_data, list):
                                existing_data = [existing_data]
                    except json.JSONDecodeError:
                        existing_data = []

                    added = 0
                    for record in new_data:
                        if not is_duplicate(existing_data, record):
                            existing_data.append(record)
                            added += 1

                    with open(json_path, 'w', encoding='utf-8') as fh:
                        json.dump(existing_data, fh, ensure_ascii=False, indent=4)
                    messages.success(request, f"Добавлено {added} новых записей в {existing_files[0]}")
                else:
                    filename = f"{uuid.uuid4().hex}.json"
                    json_path = os.path.join(JSON_DIR, filename)
                    with open(json_path, 'w', encoding='utf-8') as fh:
                        json.dump(new_data, fh, ensure_ascii=False, indent=4)
                    messages.success(request, f"Создан новый файл {filename}")

                return redirect('photometadata:index')

    # GET
    return render(request, 'photometadata/index.html', {
        'form': form,
        'upload_form': upload_form,
        'db_form': db_form,
        'csrf_token': get_token(request),
    })


# --------------------
# Список JSON-файлов
# --------------------
def json_list(request):
    """Return list of filenames (строк) из media/json."""
    folder = JSON_DIR
    files = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.lower().endswith('.json'):
                files.append(f)
    return render(request, 'photometadata/json_list.html', {
        'files': files,
        'csrf_token': get_token(request),
    })


# --------------------
# Универсальный просмотр (json list / json file / db)
# --------------------
@ensure_csrf_cookie
def view_source(request, source, filename=None):
    """
    - /view/file/ -> список файлов (json_list)
    - /view/file/<filename>/ -> содержимое файла
    - /view/db/ -> данные из БД (рендерит тот же шаблон с source_type='db')
    """
    if source == 'file':
        if not filename:
            return redirect('photometadata:json_list')
        # открыть конкретный json-файл
        json_path = os.path.join(JSON_DIR, filename)
        if not os.path.exists(json_path):
            messages.error(request, "Файл не найден.")
            return redirect('photometadata:json_list')
        try:
            with open(json_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
        except Exception:
            data = []
            messages.error(request, "Ошибка чтения JSON.")
        return render(request, 'photometadata/view_source.html', {
            'source_type': 'file',
            'data': data,
            'filename': filename,
            'csrf_token': get_token(request),
        })

    elif source == 'db':
        items = PhotoMetadata.objects.all()
        # Если источник db — используем тот же шаблон, но с source_type='db'
        return render(request, 'photometadata/view_source.html', {
            'source_type': 'db',
            'data': items,
            'csrf_token': get_token(request),
        })

    messages.error(request, "Неизвестный источник данных.")
    return redirect('photometadata:index')


# --------------------
# Просмотр БД (отдельная страница) — рендерит тот же шаблон, что и view_source source='db'
# --------------------
def db_list_view(request):
    items = PhotoMetadata.objects.all()
    return render(request, 'photometadata/db_list.html', {
        'items': items,
        'csrf_token': get_token(request),
    })


# --------------------
# AJAX: поиск, получение, обновление, удаление
# --------------------
@require_POST
def db_search_ajax(request):
    try:
        body = json.loads(request.body)
    except Exception:
        return HttpResponseBadRequest("Bad JSON")

    q = body.get('q', '').strip()
    if not q:
        return JsonResponse({'results': []})

    qs = PhotoMetadata.objects.filter(
        models.Q(title__icontains=q)
        | models.Q(photographer__icontains=q)
        | models.Q(description__icontains=q)
        | models.Q(location__icontains=q)
        | models.Q(camera__icontains=q)
        | models.Q(license__icontains=q)
        | models.Q(tags__icontains=q)
    ).values(
        'id', 'title', 'photographer', 'date_taken', 'url',
        'description', 'location', 'tags', 'width', 'height', 'camera', 'license'
    )[:200]
    return JsonResponse({'results': list(qs)})


def db_get_ajax(request, pk):
    obj = get_object_or_404(PhotoMetadata, pk=pk)
    return JsonResponse({
        'id': obj.id,
        'title': obj.title,
        'photographer': obj.photographer,
        'date_taken': obj.date_taken.isoformat() if obj.date_taken else '',
        'url': obj.url,
        'description': obj.description,
        'location': obj.location,
        'tags': obj.tags,
        'width': obj.width,
        'height': obj.height,
        'camera': obj.camera,
        'license': obj.license,
    })

def db_view_ajax(request):
    items = PhotoMetadata.objects.all().values()
    return JsonResponse({"results": list(items)})


@require_POST
def db_update_ajax(request, pk):
    """
    AJAX-обновление записи: принимает JSON с полями, обновляет запись и возвращает обновлённые данные.
    """
    obj = get_object_or_404(PhotoMetadata, pk=pk)

    try:
        body = json.loads(request.body)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Некорректный JSON: {e}'}, status=400)

    expected = [
        'title', 'photographer', 'date_taken', 'url', 'description', 'location',
        'tags', 'width', 'height', 'camera', 'license'
    ]

    data_for_form = {}
    for f in expected:
        val = body.get(f, '')
        if val is None:
            val = ''
        if f in ('width', 'height') and val != '':
            try:
                val = int(val)
            except Exception:
                val = str(val)
        data_for_form[f] = val

    form = PhotoMetaModelForm(data_for_form, instance=obj)

    if not form.is_valid():
        return JsonResponse({'ok': False, 'errors': form.errors}, status=400)

    cleaned = form.cleaned_data
    duplicates_qs = PhotoMetadata.objects.exclude(pk=pk)
    if is_duplicate(duplicates_qs, cleaned):
        return JsonResponse({'ok': False, 'error': 'Дубликат найден — обновление отменено.'}, status=409)

    try:
        updated_obj = form.save()
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Ошибка при сохранении: {e}'}, status=500)

    # Возвращаем обновлённые данные, чтобы фронтенд обновил строку без перезагрузки
    return JsonResponse({
        'ok': True,
        'item': {
            'id': updated_obj.id,
            'title': updated_obj.title,
            'photographer': updated_obj.photographer,
            'date_taken': updated_obj.date_taken.isoformat() if updated_obj.date_taken else '',
            'url': updated_obj.url,
            'description': updated_obj.description,
            'location': updated_obj.location,
            'tags': updated_obj.tags,
            'width': updated_obj.width,
            'height': updated_obj.height,
            'camera': updated_obj.camera,
            'license': updated_obj.license,
        }
    })


@require_POST
def db_delete_ajax(request, pk):
    obj = get_object_or_404(PhotoMetadata, pk=pk)
    obj.delete()
    return JsonResponse({'ok': True})

