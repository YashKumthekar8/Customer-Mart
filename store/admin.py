import imp
from multiprocessing.spawn import import_main_path
from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Product)
admin.site.register(UserTable)
admin.site.register(Cart)
admin.site.register(ViewCount)
admin.site.register(CartCount)
admin.site.register(Rating)
admin.site.register(OrderTable)