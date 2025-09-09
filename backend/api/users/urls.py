from api.users.views import SubscriptionViewSet, UserViewSet
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('users',
                UserViewSet,
                basename='users')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('users/me/avatar/',
         UserViewSet.as_view({'put': 'put_avatar',
                              'delete': 'delete_avatar'}),
         name='user-avatar'),
    path('users/subscriptions/',
         SubscriptionViewSet.as_view({'get': 'list'}),
         name='subscriptions-list'),
    path('users/<int:pk>/subscribe/',
         SubscriptionViewSet.as_view({'post': 'manage_subscription',
                                      'delete': 'manage_subscription'}),
         name='user-subscribe'),
    path('', include(router.urls)),
]
