from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm

def index(request): 
    post_list = Post.objects.order_by('-pub_date').all()
    paginator = Paginator(post_list, 5) # показывать по 5 записей на странице.
    page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    return render(request, 'index.html', {'page': page, 'paginator': paginator})
		
def group_posts(request, slug):
    # функция get_object_or_404 позволяет получить объект из базы данных 
    # по заданным критериям или вернуть сообщение об ошибке если объект не найден
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).order_by('-pub_date').all()
    paginator = Paginator(post_list, 5) # показывать по 5 записей на странице.
    page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    return render(request, 'group.html', {'group': group, 'page': page, 'paginator': paginator})

@login_required
def new_post(request):
    form_title = 'Новый пост'
    buttom_text = 'Сохранить'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            try:
                post.image=request.FILES['image']
            except:
                post.image=None
            post.save()
            return redirect('index')   
        return render(request, 'new_post.html', {'form': form, 'form_title': form_title, 'buttom_text': buttom_text})        
    form = PostForm()
    return render(request, 'new_post.html', {'form': form, 'form_title': form_title, 'buttom_text': buttom_text})

@login_required
def post_edit(request, username, post_id):
    current_user = request.user
    if current_user.username == username:
        post = get_object_or_404(Post, author=current_user, pk=post_id)
        form_title = 'Редактирование поста'         
        buttom_text = 'Изменить'
        if request.method == 'POST':
            form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
            if form.is_valid():
                post.text = form.cleaned_data['text']
                post.group = form.cleaned_data['group']
                post.save()
                return redirect('post_view', username=username, post_id=post_id)
            return render(request, 'new_post.html', {'form': form,'post': post, 'form_title': form_title, 'buttom_text': buttom_text})
        form = PostForm(instance=post)
        return render(request, 'new_post.html', {'form': form,'post': post, 'form_title': form_title, 'buttom_text': buttom_text})
    return redirect('post_view', username=username, post_id=post_id)

def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию, 
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(request, "misc/404.html", {"path": request.path}, status=404)

def server_error(request):
    return render(request, "misc/500.html", status=500)

@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post_view', username=post.author.username, post_id=post_id)
    form = CommentForm()
    return redirect('post_view', username=post.author.username, post_id=post_id)

def post_view(request, username, post_id):
    creator = get_object_or_404(User, username = username)
    posts_count = Post.objects.filter(author__username=username).count()
    post = get_object_or_404(Post, author__username=creator, id=post_id )
    form = CommentForm()
    comments = Comment.objects.filter(post=post_id)
    followers = FollowHelper.following_me_count(creator)
    ifollow = FollowHelper.i_follow_count(creator)
    return render(request, 'post.html', {
                 'form': form,
                 'creator': creator, 
                 'post': post, 
                 'comments': comments,
                 'posts_count': posts_count,
                 'followers':followers,
                 'ifollow':ifollow,
                 })
                 
class FollowHelper:
    def i_follow_count(name): # подсчет количества подписок юзера
        return Follow.objects.filter(user = name).count()

    def following_me_count(name): # подсчет количества подписчиков
        return Follow.objects.filter(author = name).count()                 
  
    def author_has_follower(request, username):
        if request.user.is_authenticated:
            author = get_object_or_404(User, username = username)
            i_follow_authors_count = Follow.objects.filter(user = request.user, author = author).count()
            if i_follow_authors_count > 0:
                return True
            else:
                return False
        else:
            return False

def profile(request, username):
    creator = get_object_or_404(User, username = username)
    post_list = Post.objects.filter(author = creator).order_by('-pub_date').all()
    paginator = Paginator(post_list, 5) # показывать по 5 записей на странице.
    page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    last_post = Post.objects.filter(author = creator).order_by('-id')[0:1]
    followers = FollowHelper.following_me_count(creator)
    ifollow = FollowHelper.i_follow_count(creator)
    is_following = FollowHelper.author_has_follower(request, username)
    return render(request, 'profile.html', {
                 'creator': creator, 
                 'page': page, 
                 'paginator': paginator, 
                 'last_post': last_post,
                 'following':is_following,
                 'followers':followers,
                 'ifollow':ifollow,
                 })

@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user).select_related('author').order_by('-pub_date').all()
    paginator = Paginator(post_list, 5) # показывать по 5 записей на странице.
    page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    return render(request, 'follow.html', {'page': page, 'paginator': paginator})

@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username = username)
    if not FollowHelper.author_has_follower(request, username) and request.user != author:
        user = get_object_or_404(User, username = request.user)
        Follow.objects.create(user = request.user, author = author)
    return redirect('profile', username = username)

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username = username)
    if FollowHelper.author_has_follower(request, username):
        Follow.objects.filter(user = request.user, author = author).delete()  
    return redirect('profile', username = username)