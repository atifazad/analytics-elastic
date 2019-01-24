from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('widget', views.widget, name='widget'),
	path('widget2', views.widget2, name='widget2'),
]
