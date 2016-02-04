from django_mongoengine import mongo_admin as admin

from tumblelog.models import BlogPost, Image, Quote, Video, Music

@admin.register(BlogPost)
class BlogPostAdmin(admin.DocumentAdmin):
    pass

@admin.register(Image)
class ImageAdmin(admin.DocumentAdmin):
    pass

@admin.register(Music)
class MusicAdmin(admin.DocumentAdmin):
    pass

@admin.register(Quote)
class QuoteAdmin(admin.DocumentAdmin):
    pass

@admin.register(Video)
class VideoAdmin(admin.DocumentAdmin):
    pass
