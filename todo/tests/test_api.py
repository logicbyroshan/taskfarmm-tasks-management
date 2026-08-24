import json
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from todo.models import Task, Category, TaskComment, PreDefinedTask

User = get_user_model()


class RestApiV1Tests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='apiuser1',
            email='apiuser1@example.com',
            password='Password123!'
        )
        self.user2 = User.objects.create_user(
            username='apiuser2',
            email='apiuser2@example.com',
            password='Password123!'
        )

        self.project1 = Category.objects.create(
            user=self.user1,
            name='User 1 Project',
            color='#3b82f6'
        )
        self.task1 = Task.objects.create(
            user=self.user1,
            category=self.project1,
            title='User 1 Task',
            status=Task.Status.TO_DO,
            priority=Task.Priority.HIGH
        )

    def test_jwt_token_obtain_and_access(self):
        # Obtain JWT
        response = self.client.post(
            reverse('api-token-obtain'),
            {'username': 'apiuser1', 'password': 'Password123!'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        access_token = response.data['access']

        # Access authenticated task endpoint with Bearer token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        tasks_res = self.client.get(reverse('api-task-list'))
        self.assertEqual(tasks_res.status_code, status.HTTP_200_OK)
        self.assertEqual(tasks_res.data['count'], 1)

    def test_task_viewset_crud_and_user_isolation(self):
        self.client.force_authenticate(user=self.user1)

        # Create Task
        create_res = self.client.post(
            reverse('api-task-list'),
            {
                'title': 'New API Task',
                'description': 'Created via DRF',
                'priority': 'moderate',
                'status': 'not-started',
                'category_id': self.project1.id
            },
            format='json'
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)
        new_task_id = create_res.data['id']

        # Detail Task
        detail_res = self.client.get(reverse('api-task-detail', args=[new_task_id]))
        self.assertEqual(detail_res.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_res.data['title'], 'New API Task')

        # Toggle Task Action
        toggle_res = self.client.post(reverse('api-task-toggle', args=[new_task_id]))
        self.assertEqual(toggle_res.status_code, status.HTTP_200_OK)
        self.assertEqual(toggle_res.data['status'], Task.Status.DONE)

        # Add Comment Action
        comment_res = self.client.post(
            reverse('api-task-comment', args=[new_task_id]),
            {'content': 'API comment'},
            format='json'
        )
        self.assertEqual(comment_res.status_code, status.HTTP_201_CREATED)

        # Update Checklist Action
        checklist_data = [{'id': 'c1', 'text': 'Subtask A', 'completed': True}]
        chk_res = self.client.post(
            reverse('api-task-checklist', args=[new_task_id]),
            {'checklist': checklist_data},
            format='json'
        )
        self.assertEqual(chk_res.status_code, status.HTTP_200_OK)

        # Verify User Isolation: User 2 cannot access or delete User 1's task
        self.client.force_authenticate(user=self.user2)
        unauth_detail = self.client.get(reverse('api-task-detail', args=[new_task_id]))
        self.assertEqual(unauth_detail.status_code, status.HTTP_404_NOT_FOUND)

        # Delete Task as User 1
        self.client.force_authenticate(user=self.user1)
        del_res = self.client.delete(reverse('api-task-detail', args=[new_task_id]))
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

    def test_project_viewset_and_stats_api(self):
        self.client.force_authenticate(user=self.user1)

        # Project List
        proj_res = self.client.get(reverse('api-project-list'))
        self.assertEqual(proj_res.status_code, status.HTTP_200_OK)

        # Stats API
        stats_res = self.client.get(reverse('api-stats'))
        self.assertEqual(stats_res.status_code, status.HTTP_200_OK)
        self.assertIn('total_count', stats_res.data['stats'])

    def test_profile_api(self):
        self.client.force_authenticate(user=self.user1)

        # Get Profile
        prof_res = self.client.get(reverse('api-profile'))
        self.assertEqual(prof_res.status_code, status.HTTP_200_OK)
        self.assertEqual(prof_res.data['username'], 'apiuser1')

        # Patch Profile
        patch_res = self.client.patch(
            reverse('api-profile'),
            {'theme': 'dark', 'notify_task_reminders': False},
            format='json'
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertFalse(patch_res.data['profile']['notify_task_reminders'])

    def test_templates_api(self):
        template = PreDefinedTask.objects.create(
            title='Configure SSL',
            category='website',
            suggested_priority='high'
        )
        self.client.force_authenticate(user=self.user1)

        # List Templates
        list_res = self.client.get(reverse('api-template-list'))
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)

        # Add Template to User Pool
        add_res = self.client.post(
            reverse('api-template-add', args=[template.id]),
            {'category_id': self.project1.id},
            format='json'
        )
        self.assertEqual(add_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Task.objects.filter(title='Configure SSL', user=self.user1).exists())

    def test_collaborator_can_access_shared_project_and_tasks_in_rest_api(self):
        # Add user2 as collaborator to user1's project
        self.project1.members.add(self.user2)

        self.client.force_authenticate(user=self.user2)

        # User2 can see shared project in CategoryViewSet
        proj_res = self.client.get(reverse('api-project-list'))
        self.assertEqual(proj_res.status_code, status.HTTP_200_OK)
        project_ids = [p['id'] for p in proj_res.data['results']]
        self.assertIn(self.project1.id, project_ids)

        # User2 can create a task in user1's shared project
        create_res = self.client.post(
            reverse('api-task-list'),
            {
                'title': 'Collaborator Task in Shared Project',
                'priority': 'high',
                'status': 'in-progress',
                'category_id': self.project1.id
            },
            format='json'
        )
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

    def test_inactive_user_token_rejection(self):
        # Create inactive user
        inactive_user = User.objects.create_user(
            username='disableduser',
            password='Password123!',
            is_active=False
        )

        from rest_framework_simplejwt.tokens import RefreshToken
        token = str(RefreshToken.for_user(inactive_user).access_token)

        # Verify token endpoint
        verify_res = self.client.post(
            reverse('api_verify_token'),
            data=json.dumps({'token': token}),
            content_type='application/json'
        )
        self.assertEqual(verify_res.status_code, 401)
        self.assertIn('disabled', verify_res.json()['error'].lower())
