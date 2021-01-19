from django.contrib import admin

# Register your models here.
from .models import Post, Group

class PostAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'text', 'pub_date', 'author') 
    # добавляем интерфейс для поиска по тексту постов
    search_fields = ('text',) 
    # добавляем возможность фильтрации по дате
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'

class GroupAdmin(admin.ModelAdmin):
    # перечисляем поля, которые должны отображаться в админке
    list_display = ('pk', 'title', 'slug', 'description') 
    # добавляем интерфейс для поиска по тексту названий групп
    search_fields = ('title',) 
    empty_value_display = '-пусто-'

# при регистрации модели Post источником конфигурации для неё назначаем класс PostAdmin
admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)