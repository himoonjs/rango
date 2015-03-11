from datetime import datetime
from django.shortcuts import render
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.bing_search import run_query


def index(request):
    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.

    category_list = Category.objects.order_by('-likes')[:5]
    most_viewed_page_list = Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'most_viewd_pages': most_viewed_page_list}

    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False

    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

        if (datetime.now() - last_visit_time).seconds > 5:
            # ...reassign the value of the cookie to +1 of what it was before...
            visits = visits + 1
            # ...and update the last visit cookie, too.
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time.
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits

    response = render(request, 'rango/index.html', context_dict)

    return response

def about(request):
    # If the visits session varible exists, take it and use it.
    # If it doesn't, we haven't visited the site so set the count to zero.
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0

    context_dict = {'about_text': "Rango says this is the about page.", 'visits': count}

    return render(request, 'rango/about.html', context_dict)
    #return HttpResponse("Rango says here is the about page.<br/><a href='/rango/'>Index</a>")

def category(request, category_name_slug):
    context_dict = {}
    context_dict['result_list'] = None
    context_dict['query'] = None
    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)

            context_dict['result_list'] = result_list
            context_dict['query'] = query

    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name
        pages = Page.objects.filter(category=category).order_by('-views')
        context_dict['pages'] = pages
        context_dict['category'] = category
        context_dict['category_name_slug'] = category.slug
    except Category.DoesNotExist:
        pass

    if not context_dict['query']:
        context_dict['query'] = category.name

    return render(request, 'rango/category.html', context_dict)




@login_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()

    return render(request, 'rango/add_category.html', {'form': form})

@login_required
def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        form = PageForm()

    context_dict = {'form':form, 'category': cat}

    return render(request, 'rango/add_page.html', context_dict)

@login_required
def restricted(request):
    return render(request, 'rango/restricted.html', {})

def track_url(request):
    page_id = None
    url ='/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)

def register_profile(request):

    if request.method == 'POST':
        profile_form = UserProfileForm(data=request.POST)
        new_profile = profile_form.save(commit=False)
        user = User.objects.get(id=request.user.id)
        new_profile.user = user
        new_profile.picture = request.FILES['picture']
        new_profile.save()
        return index(request)
    else:
        profile_form = UserProfileForm(request.GET)

    return render(request, 'rango/profile_registration.html', {'profile_form': profile_form})

@login_required
def view_profile(request, username):
    context_dict = {}
    user = User.objects.get(username=username)

    try:
        user_profile = UserProfile.objects.get(user=user)
    except:
        user_profile = None

    context_dict['username'] = username
    context_dict['user_profile'] = user_profile
    context_dict['user'] = user

    return render(request, 'rango/profile.html', context_dict)

def profile(request):
    return redirect('/rango/view_profile/'+request.user.username+"/")

@login_required
def users_profile(request):
    context_dict = {}
    users = User.objects.all()

    context_dict['users'] = users
    return render(request, 'rango/users_profile.html', context_dict)

@login_required
def edit_profile(request):
    user = User.objects.get(username=request.user)

    try:
        user_profile = UserProfile.objects.get(user=user)

    except:
        user = None

    if request.method == 'GET':
        edit_profile_form = UserProfileForm(request.GET)
        context_dict = {}
        context_dict['edit_profile_form'] = edit_profile_form
        context_dict['user'] = user
        context_dict['user_profile'] = user_profile
        return render(request, 'rango/edit_profile.html', context_dict)

    if request.method == 'POST':
        try:
            user_profile.picture = request.FILES['picture']
        except:
            user_profile.picture = '/static/images/about.jpg'
        user_profile.website = request.POST['website']
        user_profile.save()
        return profile(request)

@login_required
def like_category(request):

    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes + 1
            cat.likes = likes
            cat.save()

    return HttpResponse(likes)

def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    if starts_with:
        cat_list = Category.objects.filter(name__istartswith=starts_with)

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]

    return cat_list

def suggest_category(request):

    cat_list = []
    starts_with = ''
    if request.method == 'GET':
        starts_with = request.GET['suggestion']

    cat_list = get_category_list(8, starts_with)

    return render(request, 'rango/cats.html', {'cats': cat_list})

@login_required
def auto_add_page(request):
    cat_id = None
    url = None
    title = None
    context_dict = {}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url = request.GET['url']
        title = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)

            pages = Page.objects.filter(category=category).order_by('-views')

            # Adds our results list to the template context under name pages.
            context_dict['pages'] = pages

    return render(request, 'rango/page_list.html', context_dict)



