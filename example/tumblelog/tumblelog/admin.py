from django_mongoengine import mongo_admin as admin

from tumblelog.models import BlogPost, Image, Quote, Video, Music


class BlogPostAdmin(admin.DocumentAdmin):
    pass


class ImageAdmin(admin.DocumentAdmin):
    pass


class MusicAdmin(admin.DocumentAdmin):
    pass


class QuoteAdmin(admin.DocumentAdmin):
    pass


class VideoAdmin(admin.DocumentAdmin):
    pass


admin.site.register(BlogPost, BlogPostAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Quote, QuoteAdmin)
admin.site.register(Video, VideoAdmin)
admin.site.register(Music, MusicAdmin)
