from django.urls import path
from . import views

app_name = 'photometadata'

urlpatterns = [
    path('', views.index, name='index'),                    # Главная — форма и загрузка

    # JSON-файлы: список и открытие конкретного
    path('json/', views.json_list, name='json_list'),
    path('view/<str:source>/', views.view_source, name='view_source'),  # /view/file/ или /view/db/
    path('view/<str:source>/<str:filename>/', views.view_source, name='view_source_file'),

    # Отдельная страница для просмотра БД (может совпадать с view_source source='db')
    path('db/', views.db_list_view, name='db_list'),
    path("db/update/<int:pk>/", views.db_update_ajax, name="db_update_ajax"),


    # AJAX
    path('ajax/search/', views.db_search_ajax, name='db_search_ajax'),
    path('ajax/get/<int:pk>/', views.db_get_ajax, name='db_get_ajax'),
    path('ajax/update/<int:pk>/', views.db_update_ajax, name='db_update_ajax'),
    path('ajax/delete/<int:pk>/', views.db_delete_ajax, name='db_delete_ajax'),
    path("ajax/view/", views.db_view_ajax, name="db_view_ajax"),

]




