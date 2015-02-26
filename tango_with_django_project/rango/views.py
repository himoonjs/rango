from django.shortcuts import render
from django.http import HttpResponse

from rango.models import Category
from rango.models import Page

def index(request):
	# Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.

    context_dict = {}

    category_list = Category.objects.order_by('-likes')[:5]
    context_dict['categories'] = category_list

    most_viewd_page_list = Page.objects.order_by('-views')[:5]
    context_dict['most_viewd_pages'] = most_viewd_page_list

    # Render the response and send it back!
    return render(request, 'rango/index.html', context_dict)

def about(request):

	context_dict = {'linktoindex': "Rango says this is the about page."}

	return render(request, 'rango/about.html', context_dict)
	#return HttpResponse("Rango says here is the about page.<br/><a href='/rango/'>Index</a>")

def category(request, category_name_slug):

	context_dict = {}

	try:
		category = Category.objects.get(slug=category_name_slug)
		context_dict['category_name'] = category.name

		pages = Page.objects.filter(category=category)
		context_dict['pages'] = pages
		context_dict['category'] = category
	except Category.DoesNotExist:
		pass
	return render(request, 'rango/category.html', context_dict)