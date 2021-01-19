from django.test import TestCase
from django.test.client import Client
from .models import User, Post, Comment

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

class TestPostAndComment(TestCase):
    def setUp(self):
        client = Client()
        self.user = User.objects.create_user(username='test', email='test@email.com', password='$12345qwerty$')
        self.post_text = 'Testing'
        self.post = Post.objects.create(text=self.post_text, author=self.user)
        self.n_post_id = self.post.id

# 	После регистрации пользователя создается его персональная страница (profile)
    def test_newuser_profile(self):
        response = self.client.get('/test/')
        self.assertContains(response, 'test', status_code=200, msg_prefix='', html=False)

#   Неавторизованный посетитель не может опубликовать пост (его редиректит на страницу входа)
    def test_non_auth_user_fail(self):
        response = self.client.get('/new/', follow=True)
        self.assertContains(response, 'Войти на сайт', status_code=200, msg_prefix='', html=False)   

# 	Авторизованный пользователь может опубликовать пост (new)
    def test_newpost_create(self):         
        self.client.login(username='test', password='$12345qwerty$')
        response = self.client.post('/new/', 
                                   {'text': self.post_text, 'author':self.user}, 
                                   follow=True)
        self.assertEqual(response.status_code, 200)
        post_count = Post.objects.filter(text = self.post_text).count()
        self.assertEqual(post_count, 2)

# После публикации поста новая запись появляется на...
    def test_newpost_index_page(self):
        response = self.client.get('/') # ... на главной странице сайта (index)
        self.assertContains(response, self.post_text, count=2, status_code=200, msg_prefix='', html=False)

    def test_newpost_profile_page(self):
        response = self.client.get('/test/')    # ... на персональной странице пользователя (profile)
        self.assertContains(response, self.post_text, count=2, status_code=200, msg_prefix='', html=False)
    
    def test_newpost_post_page(self):
        response = self.client.get(f'/test/{self.n_post_id}/')  # ... на отдельной странице поста (post)
        self.assertContains(response, self.post_text, count=1, status_code=200, msg_prefix='', html=False)
       
# Авторизованный пользователь может отредактировать свой пост и он изменится в БД
    def test_editpost_appear(self):
        post_text = 'Edited'
        self.client.login(username='test', password='$12345qwerty$')
        response = self.client.post(f'/test/{self.n_post_id}/edit/', 
                                   {'text': post_text , 'author': self.user}, 
                                   follow=True)
        post_count = Post.objects.filter(id = self.n_post_id, text = post_text).count()                                 
        self.assertEqual(post_count, 1)

	# возвращает ли сервер код 404, если страница не найдена
    def test_404_page(self):         
        response = self.client.post('/jlkjklfjdgjfdgklfklghhdchdhd/', 
                                   {'text': self.post_text, 'author':self.user}, 
                                   follow=True)
        self.assertEqual(response.status_code, 404)

    def test_AU_comment_in_db(self): #можно комментировать. Коммент попадает в базу.
        self.client.login(username='test', password='$12345qwerty$')
        response = self.client.post('/new/', 
                                   {'text': 'PostText', 'author':self.user}, 
                                   follow=True)
        self.client.post('/test/1/comment/', {'text' : 'TestСomment'})
        comment_count = Comment.objects.filter(text = 'TestСomment').count()
        self.assertEqual(comment_count, 1)

    def test_AU_comment(self): # добавление коммента на страницу
        self.client.login(username='test', password='$12345qwerty$')
        response = self.client.post('/new/', 
                                   {'text': 'PostText', 'author':self.user}, 
                                   follow=True)
        self.client.post('/test/1/comment/', {'text' : 'TestСomment'})
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/test/1/')
        self.assertContains(response, 'TestСomment', status_code=200)

    

class TestIMG(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='test2', email='test@email.com', password='$12345qwerty$')
        self.post_text = 'Testing 1234567890'
        self.post = Post.objects.create(text=self.post_text, author=self.user)
        self.n_post_id = self.post.id
        self.client.login(username='test2', password='$12345qwerty$')
        with open('media/test/test2.jpg', 'rb') as fp: 
            self.client.post('/new/', {'text': self.post_text, 'image': fp})

# После публикации поста IMG появляется на...
    def test_img_index_page(self):# ... на главной странице сайта (index)
        response = self.client.get('/') 
        self.assertContains(response, '<img', status_code=200 )

    def test_img_profile_page(self):# ... на персональной странице пользователя (profile)
        response = self.client.get('/test2/')    
        self.assertContains(response, '<img', status_code=200 )
    
    def test_img_post_page(self):# ... на отдельной странице поста (post)
        response = self.client.get(f'/test2/2/')  
        self.assertContains(response, '<img ', status_code=200 )

    # срабатывает защита от загрузки файлов не-графических форматов
    def test_non_img(self):
        response = self.client.get(f'/test2/2/')
        with open('media/test/test1.txt', 'rb') as fp: 
            self.client.post('/test2/2/', {'text': self.post_text, 'image': fp})  
        self.assertContains(response, '<img ', status_code=200 )

class TestFollowings(TestCase):
    
    def setUp(self):
        client = Client()
        self.user = User.objects.create_user(username='testuser', email='testuser@email.com', password='$12345qwerty$')
        self.author = User.objects.create_user(username='testauthor', email='testauthor@email.com', password='$12345qwerty$')
        self.post_text = 'Testing2'
        self.post = Post.objects.create(text=self.post_text, author=self.user)
    
    def test_non_AU_follow(self):# Попытка подписаться неавторизованного пользователя
        response = self.client.get('/testuser/follow') 
        self.assertNotContains(response, 'Отписаться', status_code=302)

    def test_AU_follow(self): # Попытка подписаться авторизованного пользователя
        self.client.login(username='testuser', password='$12345qwerty$')
        response = self.client.get('/testuser/follow')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/testuser/')
        response = self.client.get('/testuser/unfollow')
        self.assertNotContains(response, 'Отписаться', status_code=302)

    def test_AU_unfollow(self): # Попытка отписаться авторизованного пользователя
        self.client.login(username='testuser', password='$12345qwerty$')
        response = self.client.get('/testuser/follow')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/testuser/')
        response = self.client.get('/testuser/unfollow')
        self.assertNotContains(response, 'Подписаться', status_code=302)

    def test_new_post_see_only_followers(self): # Юзер видит на вкладе "Избранные авторы" новый пост автора, на которого он подписан.
        self.client.login(username='testuser', password='$12345qwerty$')
        self.client.get('/testauthor/follow')
        self.post_text = 'Testing_NewPostCanSeeFollowersOnly'
        self.post = Post.objects.create(text=self.post_text, author=self.author)
        response = self.client.get('/follow/')
        self.assertContains(response, self.post_text)

    def test_new_post_dont_see_not_followers(self): # Юзер не видит на вкладе "Избранные авторы" новый пост автора, на которого он не подписан.
        self.author2 = User.objects.create_user(username='testauthor2', email='testauthor2@email.com', password='$12345qwerty$')
        self.client.login(username='testuser', password='$12345qwerty$')
        self.client.get('/testauthor/follow')
        self.post_text1 = 'Testing_NewPostCanSeeFollowersOnly'
        self.post = Post.objects.create(text=self.post_text1, author=self.author)
        self.post_text2 = 'Testing_NewPostCanSeeFollowersOnly-2'
        self.post = Post.objects.create(text=self.post_text2, author=self.author2)
        response = self.client.get('/follow/')
        self.assertContains(response, self.post_text1)
        self.assertNotContains(response, self.post_text2)
        