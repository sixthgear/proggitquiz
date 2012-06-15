from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('pq.views',
    (r'^$',                                                         'home'),
    (r'^challenge/$',                                               'challenge_list'),
    (r'^challenge/(?P<problem>\d+)/$',                              'challenge'),
    (r'^challenge/(?P<problem>\d+)/begin/(?P<set>\d+)/$',           'solution_begin'),
    (r'^challenge/(?P<problem>\d+)/(?P<solution>\d+)/upload/$',     'solution_upload'),
    (r'^rules/',                                                    'rules'),
    (r'^contribute/',                                               'contribute'),
    (r'^users/me/',                                                 'user_profile'),
    (r'^users/(?P<username>\w+)/',                                  'user_profile'),
)

urlpatterns += patterns('',
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'media/'}),
)
