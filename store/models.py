from jsonfield import JSONField
from django.db import models


class Product(models.Model):
    pid= models.AutoField(primary_key=True)
    pname = models.CharField(max_length=100,null=False)
    section = models.CharField(max_length=100,null=False)
    subsection = models.CharField(max_length=100,null=False)
    price=models.IntegerField(null=False)
    company=models.CharField(max_length=100,null=False)
    desc=models.CharField(max_length=10000,null=False)
    url1=models.CharField(max_length=10000)
    url2=models.CharField(max_length=10000)
    url3=models.CharField(max_length=10000)


class UserTable(models.Model):
    email = models.EmailField()
    phone_no = models.CharField(max_length = 20)
    address = models.CharField(max_length = 100)
    password = models.CharField(max_length=100)
    username = models.CharField(max_length = 50)    


class Cart(models.Model):
     username= models.CharField(max_length = 50)
     plist=JSONField()

class CartCount(models.Model):
     pname = models.CharField(max_length=100,null=False)
     count=models.BigIntegerField()    

class ViewCount(models.Model):
     pname = models.CharField(max_length=100,null=False)
     count=models.BigIntegerField()     

class Rating(models.Model):
     username=models.CharField(max_length = 50)    
     pname=models.CharField(max_length=100,null=False)
     rating=models.BigIntegerField()  