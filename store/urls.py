from django.urls import path,include
from . import views

urlpatterns = [
    path('', views.home, name='store-home'),
    path('login/', views.login, name='store-login'),

    path('register/',views.register,name='store-register'),
    path('register/<str:username>',views.registerUserdetails,name='store-user-details'),
    
    path('about-us/',views.AboutUs,name='store-about-us'),
    
    path('section/<str:SectionName>/',views.section,name='store-section'),
    path('section/<str:SectionName>/subsection/<str:subsection>/',views.subsection,name='store-subsection'),
    path('section/<str:SectionName>/subsection/<str:subsection>/<str:pname>/',views.productPage,name='store-product'),
    
    path('accounts/', include('allauth.urls')),
    
    path('cart/',views.Cartfunction,name="store-cart"),
    path('addTocart/<int:pid>/',views.AddCart,name="AddTo-store-cart"),
    path('removeCart/<str:pname>/<int:quantity>/',views.RemoveCart,name="RemoveTo-store-cart"),

    path('logout/', views.Logout, name ='logout'),
    path('profile/', views.Profile, name ='logout'),

]