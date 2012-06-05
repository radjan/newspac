from django.conf.urls.defaults import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'newspacks.views.home', name='home'),
    # url(r'^newspacks/', include('newspacks.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^topic$', 'views.topic'), 
    url(r'^article$', 'views.article'), 
    url(r'^topic_ana$', 'views.topic_ana'), 
    url(r'^power_price$', 'views.power_price'), 
)
urlpatterns += staticfiles_urlpatterns()
urlpatterns += patterns('',
    url(r'.*', 'views.index'),  
)

