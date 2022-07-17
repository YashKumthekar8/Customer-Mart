from curses import use_default_colors
import imp
from multiprocessing import context
from pickle import NONE
import re
from django.shortcuts import redirect, render
from django.http import HttpResponse
from .models import *
from django.contrib.auth import logout
from .forms import *
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth import authenticate
from django.contrib import auth
from django.contrib.auth.models import User



#Function for returning the section,subsection,product name and url
def ListOfProducts():
    NameList=[]
    obj=Product.objects.all()
    tempList=[]

    for itr in obj:
        #Adding the section name
        if str(itr.section) not in tempList:
            temp=[]
            tempList.append(str(itr.section))
            temp.append(str(itr.section))
            temp.append(f'/section/{itr.section}')
            NameList.append(temp)

        #Adding the subsection name
        if str(itr.subsection) not in tempList:
            temp=[]
            tempList.append(str(itr.subsection))
            temp.append(str(itr.subsection))
            temp.append(f'/section/{itr.section}/subsection/{itr.subsection}/')
            NameList.append(temp)

        #Adding the product name
        if str(itr.pname) not in tempList:
            temp=[]
            tempList.append(str(itr.pname))
            temp.append(str(itr.pname))
            temp.append(f'/section/{itr.section}/subsection/{itr.subsection}/{itr.pname}/')
            NameList.append(temp)

    return NameList


#Function for the home page
def home(request):

    #To check if user is logged in or not
    logged_in=False
    if request.user.is_authenticated:
        logged_in=True
    
    user=str(request.user)
    #Checking if user is logged in through googel then fecthing the address
    obj=UserTable.objects.filter(username=user)
    if len(obj)==0 and logged_in:
      #Means the user is signed Up through google
      return redirect(f'register/{user}')    

    #All objects
    obj=Product.objects.all()
    

    Section=set()
    SectionObject=[]
    #Getting all the sections
    for itr in obj:
       if itr.section not in Section: 
        Section.add(itr.section)
        SectionObject.append(itr)
    
    ProductList=ListOfProducts

    context={
        'object':SectionObject,
        'logged_in':logged_in,
        'productList':ProductList
    }    
    return render(request, 'index.html',context)


#For the login page
def login(request):
    if request.method=='POST':
        form=authenticate(username=request.POST.get('username'), password=request.POST.get('password'))
        if form is not None:
            auth.login(request,form)
            return redirect('store-home')
        else:
             return render(request,'login.html',{'error':"Invalid Username or password"})   
    else:
      return render(request,'login.html')    


#For registering the new user
def register(request):

    if request.method=='POST':

        form=UserForm(request.POST)
        if  form.is_valid():
            #Adding the username and password in the user table
            data={
                'username':request.POST.get('username'),
                'password1':request.POST.get('password'),
                'password2':request.POST.get('password')
            }
            
            form1=UserCreationForm(data=data)
            #If data is correct saving the user details
            if form1.is_valid():
                form1.save()
                form.save()
                return redirect('store-login')
            #Throwing the error    
            else: 
                return render(request,'register.html',{'error':form1.errors.values()})   
    else:
      return render(request,'register.html')      



def AboutUs(request):
    ProductList=ListOfProducts
    return render(request,'about-us.html',{'productList':ProductList})


#Function for displaying the product of the particular section
def section(request,SectionName):

    #To check if user is logged in or not
    logged_in=False
    if request.user.is_authenticated:
        logged_in=True
        print(UserTable.objects.filter(username=str(request.user))[0].id)

    obj=Product.objects.filter(section=SectionName)
    subSection=set()
    subSectionObject=[]
    
    #Getting all the subsections
    for itr in obj:
       if itr.subsection not in subSection: 
          subSection.add(itr.subsection)
          subSectionObject.append(itr)
    
    ProductList=ListOfProducts
    context={
         'object':subSectionObject,
          'logged_in':logged_in,
        'productList':ProductList
    }
    return render(request,'category_main.html',context)     


#Functuon for rendering the list of product in that particular section and subsection with and without filters
def subsection(request,SectionName,subsection):
    ProductList=ListOfProducts
    #If filters are applied  on company or the price of the product
    if request.method=='POST':
        
        logged_in=False
        if request.user.is_authenticated:
            logged_in=True

        obj=Product.objects.filter(section=SectionName,subsection=subsection)
        
        #Getting the comapny which user has selected to filter
        cmpy=[]
        for itr in obj:
          if itr.company in request.POST:
                cmpy.append(itr.company)
        
        #Getting the range of amount entered by the user
        string=str(request.POST.get("amountRange"))
        idx=string.find('-')
        s1=string[:idx]
        s2=string[idx+2:]
        
        #Start point of the range
        minPrice=int(s1[s1.find(' ')+1:])
        
        #End point of the range
        maxPrice=int(s2[s2.find(' ')+1:])

        #Filtering the products that satisfy the current filters 
        finalObject=[]
        for itr in obj:
            if itr.price>=minPrice and itr.price<=maxPrice and itr.company in cmpy:
                finalObject.append(itr)
        
        #If no product matches the current filter
        if len(finalObject)==0:
            context={
            'object':finalObject,
            'company':cmpy,
            'section':SectionName,
            'subsection':subsection,
            'logged_in':logged_in,
            'minPrice':minPrice,
             'maxPrice':maxPrice,
             'message':"No product matched" ,
             'productList':ProductList
            }    
            return render(request,'category.html',context)
        
        #If some products matches the current filter
        else:
            context={
                'object':finalObject,
                'company':cmpy,
                'section':SectionName,
                'subsection':subsection,
                'logged_in':logged_in,
                'minPrice':minPrice,
                'maxPrice':maxPrice, 
                'productList':ProductList
            }    
            return render(request,'category.html',context)
        
    #If filters are not applied
    else:  
        #To check if user is logged in or not
        logged_in=False
        if request.user.is_authenticated:
            logged_in=True

        obj=Product.objects.filter(section=SectionName,subsection=subsection)
        cmpy=set()
        minPrice=obj[0].price
        maxPrice=0
        for itr in obj:
            cmpy.add(itr.company)
            minPrice=min(minPrice,itr.price)
            maxPrice=max(maxPrice,itr.price)
        
        context={
            'object':obj,
            'company':cmpy,
            'section':SectionName,
            'subsection':subsection,
            'logged_in':logged_in,
            'minPrice':minPrice,
             'maxPrice':maxPrice, 
             'productList':ProductList
        }    
        return render(request,'category.html',context)
    

#For the product  page
def productPage(request,SectionName,subsection,pname):
    #To check if user is logged in or not
    logged_in=False
    ProductList=ListOfProducts
    if request.user.is_authenticated:
        logged_in=True
        
        #If the product is visited for first time
        if len(ViewCount.objects.filter(pname=pname))!=0:
            count=ViewCount.objects.filter(pname=pname)[0].count+1
            ViewCount.objects.filter(pname=pname).update(count=count)
        else:
           obj=ViewCount(pname=pname,count=1)
           obj.save()

    #If the user has provided the rating to the current product
    if request.method=='POST':
        
        rating=request.POST.get('rate')
        obj=Product.objects.filter(section=SectionName,subsection=subsection,pname=pname)
        
        if logged_in:
                id=UserTable.objects.filter(username=str(request.user))[0].id
                obj1=Rating.objects.filter(userid=id,pname=pname)

                #If the user has changed the rating
                if len(obj1)!=0:
                    Rating.objects.filter(userid=id,pname=pname,subsection=subsection).update(rating=rating)
                #User is rating for first time
                else:   
                       obj1=Rating(userid=id,pname=pname,rating=rating,subsection=subsection)
                       obj1.save()

                context={
                    'object':obj,
                    'section':SectionName,
                    'subsection':subsection,
                    'logged_in':logged_in,
                    'rating':int(rating),
                    'productList':ProductList
                }    
                return render(request,'productpage.html',context)   
        else:
            return redirect('store-login')

    #Render the product page
    else:
        obj=Product.objects.filter(section=SectionName,subsection=subsection,pname=pname)
        rating=0

        #If the user is logged in getting the rating of the product
        id=UserTable.objects.filter(username=str(request.user))[0].id
        rating=0
        obj1=Rating.objects.filter(userid=id,pname=pname)
        if logged_in and len(obj1)!=0:
            rating=obj1[0].rating

        context={
            'object':obj,
            'section':SectionName,
            'subsection':subsection,
            'logged_in':logged_in,
            'rating':rating,
            'productList':ProductList
        }    
        return render(request,'productpage.html',context)   


def Logout(request):
    logout(request)
    return redirect('/')    


#For displaying the cart fo the particular user
def Cartfunction(request):
    ProductList=ListOfProducts
    #To check if user is logged in or not and if user is not logged in redirect to login page
    if not  request.user.is_authenticated:
        return redirect('store-login')
    else:  
      user=str(request.user)  

      #Fetching the items purchased in the cart of the current user
      obj=Cart.objects.filter(username=user)  
      #If cart is empty
      if len(obj) == 0 or len(obj[0].plist)==0:
         return render(request,'cart.html',{"message":"Your cart is empty",'productList':ProductList}) 
      else:

         #Fetching the quantity and total products in the carts
         pidList=obj[0].plist.keys()
         productList=[] 
         totalQuantity=0
         totalPrice=0

         for itr in pidList:
            temp=[]

            #Quantity of the current item
            totalQuantity+=obj[0].plist[itr]
            temp.append(obj[0].plist[itr])
            
            #Product details of the current product
            temp.append(Product.objects.filter(pid=str(itr))[0])  
            totalPrice+=temp[1].price*temp[0]
            productList.append(temp)
         
         context={
              'object':productList,
              'noOfProduct':len(productList),
              'quantity':totalQuantity,
              'price':totalPrice,
              'productList':ProductList
         }   
         return render(request,'cart.html',context)     


#Function for adding the product to the cart
def AddCart(request,pid):
    
    #To check if user is logged in or not and if user is not logged in redirect to login page
     if not  request.user.is_authenticated:
        return redirect('store-login')
     else:
       pname=Product.objects.filter(pid=pid)[0].pname 
       
       #If the product is added to cart  for first time then adding the cart count
       if len(CartCount.objects.filter(pname=pname))!=0:
            count=CartCount.objects.filter(pname=pname)[0].count+1
            CartCount.objects.filter(pname=pname).update(count=count)
       else:
           obj=CartCount(pname=pname,count=1)
           obj.save() 

       user=str(request.user)
       obj=Cart.objects.filter(username=user)
        
       #If user has already items in cart than add current item
       if len(obj)!=0:
            plist=obj[0].plist
            if str(pid) in plist.keys():
                plist[str(pid)]=plist[str(pid)]+1
            else:
               plist[str(pid)]=1
            Cart.objects.filter(username=user).update(plist=plist)        
       #Adding the user first time in the cart
       else:
           obj=Cart(username=user,plist={str(pid):1})
           obj.save()

       return redirect('store-cart')      



def Profile(request):
    return render(request,'profile.html')      



#Getting the address and phone number of google logined user
def registerUserdetails(request,username):
    if request.method=='POST':
        form=UserForm(request.POST)
        if  form.is_valid():
           form.save()
           return redirect('store-home')
        
        else: 
            return render(request,'register.html',{'error':form.errors.values(),'username':username})   
 
    else:
      return render(request,'register.html',{'username':username})      




#Removing the product from the cart
def RemoveCart(request,pname,quantity):
   ProductList=ListOfProducts
   if request.method=='POST': 
        remQuantity=int(request.POST.get('remQuantity'))
        #Geting the user
        username=request.user
        
        obj=Product.objects.filter(pname=pname)
        pid=obj[0].pid

        #Getting the cart object
        obj=Cart.objects.filter(username=username)

        
        productList=dict(obj[0].plist)
        quantityAvailable=productList[str(pid)]

        #Case of removing the product from the cart
        if remQuantity==quantityAvailable:
            del productList[str(pid)]
            Cart.objects.filter(username=username).update(plist=productList)
        #Case of removing the quantity of product from cart
        else:
            productList[str(pid)]=quantityAvailable-remQuantity
            Cart.objects.filter(username=username).update(plist=productList)
        
        #Redirecting to the cart page
        return redirect("store-cart")

   else: 
        context={
            'pname':pname,
            'quantity':quantity,
            'productList':ProductList
        }
        return render(request,'removeCart.html',context)