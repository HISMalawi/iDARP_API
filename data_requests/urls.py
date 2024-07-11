from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'equipment-type', views.EquipmentTypeView)
router.register(r'irb', views.IRBViewSet)

urlpatterns = [
    path('', views.DataRequestView.as_view(), name='data-request'),
    path('allrequest/', views.GetUserRequest.as_view()),
    path('guest/', views.SubmitDataRequestView.as_view()),
    path('<int:pk>/', views.DataRequestView.as_view()),
    path('history/', views.DataRequestHistoryView.as_view()),
    path('purposes/', views.PurposeView.as_view()),
    path('dataset_presets/', views.DatasetPresetView.as_view()),
    path('requested_datasets/', views.RequestedDatasetView.as_view(), name='requested-datasets'),
    path('create_requested_datasets/', views.PostRequestedDatasetView.as_view()),
    path('dataset_variables/', views.DatasetVariableView.as_view()),
    path('request_state/<int:pk>/', views.DataRequestStateView.as_view()),
    path('request_edges/', views.DataRequestEdgeView.as_view()),
    path('delete_request/<int:pk>/', views.DataRequestDeleteView.as_view()),
    path('retrieve_file/<path:file_url>/', views.FileRetrieveView.as_view(), name='retrieve_file'),
    path('file_access/<path:file_url>/', views.FileAccessView.as_view(), name='file_access'),
    path('data_handling_devices/', views.DataHandlingDeviceList.as_view(), name='data_handling_devices'),
    path('staff_shared/', views.StaffSharedList.as_view(), name='staff_shared'),
    path('statecomment/add', views.StateCommentCreateView.as_view()),
    path('statecomment/update/<int:comment_id>', views.StateCommentUpdateView.as_view()),
    path('statecomment', views.StateCommentListView.as_view()),
    path('statecomment/list/<int:data_request_id>/', views.StateCommentListByRequestView.as_view(), name='statecomment-list'),
    path('statecomment/section/', views.StateCommentListBySectionView.as_view(), name='state_comment_list'),
    path('statecomment/all-sections/', views.StateCommentAllSectionsListView.as_view(), name='state_comment_sections'),
    path('statecomment/<int:pk>/', views.StateCommentDetailView.as_view()),
    path('reply/add', views.ReplyCreateView.as_view()),
    path('reply/update', views.ReplyUpdateView.as_view()),
    path('reply', views.ReplyListView.as_view()),
    path('reply/<int:pk>/', views.ReplyDetailView.as_view()),
    path('reply/list/<int:comment_id>/', views.ReplyListByStateCommentView.as_view(), name='reply-list'),
    path('download-request/<int:request_id>/', views.DownloadRequestView.as_view(), name='download-request'),
    path('patch/requested_dataset/<int:pk>/', views.RequestedDatasetPatchView.as_view(), name='PatchRequestedDataset'),
    path('patch/data_request/<int:pk>/', views.DataRequestPatchView.as_view(), name='PatchDataRequest'),
    path('patch/data_request_docs/<int:pk>/', views.EthicsDocPatchPatchView.as_view(), name='PatchDataRequest'),
    path('patch/dataset_variable/<int:pk>/', views.DatasetVariablePatchView.as_view(), name='PatchDatasetVariable'),
    path('patch/data_handling_devices/<int:pk>/', views.DataHandlingDevicesPatchView.as_view(), name='PatchDataHandlingDevices'),
    path('patch/staff_shared/<int:pk>/', views.StaffSharedPatchView.as_view(), name='PatchStaffShared'),
    path('soft_delete/data_handling_devices/<int:pk>/', views.DataHandlingDeviceDeleteView.as_view(), name='data-handling-device-delete'),
    path('soft_delete/staff_shared/<int:pk>/', views.StaffSharedDeleteView.as_view(), name='staff-shared-delete'),
    path('data-handling-device/', views.DataHandlingDeviceCreateView.as_view(), name='data-handling-device-create'),
    path('staff-shared/', views.StaffSharedCreateView.as_view(), name='staff-shared-create'),
]
urlpatterns += router.urls
