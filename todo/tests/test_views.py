import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from todo.models import Task, Category, PreDefinedTask

User = get_user_model()


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewuser',
            email='viewuser@example.com',
            password='password123'
        )
        self.client.force_login(self.user)
        self.project = Category.objects.create(
            user=self.user,
            name='Test Project',
            color='#3b82f6'
        )
        self.task = Task.objects.create(
            user=self.user,
            category=self.project,
            title='Initial Task',
            status=Task.Status.TO_DO,
            priority=Task.Priority.MODERATE
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todo/index.html')
        self.assertIn('total_count', response.context)
        self.assertIn('due_today_count', response.context)
        self.assertIn('all_projects_progress', response.context)
        self.assertIn('recently_completed_tasks', response.context)

    def test_manage_tasks_view_and_htmx(self):
        response = self.client.get(reverse('manage_tasks'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todo/manage-tasks.html')

        # HTMX partial response
        htmx_response = self.client.get(
            reverse('manage_tasks'),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(htmx_response.status_code, 200)
        self.assertTemplateUsed(htmx_response, 'todo/components/task_list_partial.html')

    def test_manage_kanban_view(self):
        response = self.client.get(reverse('manage_kanban'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todo/kanban.html')

    def test_manage_projects_view(self):
        response = self.client.get(reverse('manage_projects'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'todo/manage-projects.html')

    def test_task_create_via_ajax(self):
        payload = {
            'title': 'New AJAX Task',
            'description': 'Created via test',
            'priority': 'high',
            'status': 'not-started',
            'category': self.project.id
        }
        response = self.client.post(reverse('task_create'), data=payload, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(Task.objects.filter(title='New AJAX Task').exists())

    def test_task_update_json_and_status(self):
        # JSON body partial update
        update_data = {'title': 'Updated Title', 'status': 'completed'}
        response = self.client.post(
            reverse('task_update', args=[self.task.id]),
            data=json.dumps(update_data),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Title')
        self.assertEqual(self.task.status, Task.Status.DONE)

    def test_task_toggle_status(self):
        response = self.client.post(
            reverse('task_toggle_status', args=[self.task.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, Task.Status.DONE)

    def test_task_add_comment_view(self):
        response = self.client.post(
            reverse('task_add_comment', args=[self.task.id]),
            data=json.dumps({'content': 'View comment test'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.task.comments.count(), 1)

    def test_task_delete_comment_view(self):
        # Create comment
        res = self.client.post(
            reverse('task_add_comment', args=[self.task.id]),
            data=json.dumps({'content': 'Comment to delete'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        comment_id = res.json()['comment']['id']
        del_res = self.client.post(
            reverse('task_comment_delete', args=[comment_id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(self.task.comments.count(), 0)

    def test_task_update_checklist_view(self):
        checklist = [{'id': 'c1', 'text': 'Checklist item', 'completed': False}]
        response = self.client.post(
            reverse('task_update_checklist', args=[self.task.id]),
            data=json.dumps({'checklist': checklist}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.checklist, checklist)

    def test_category_create_and_delete(self):
        # Create
        response = self.client.post(
            reverse('category_create'),
            data={'name': 'Marketing App', 'color': '#ef4444', 'description': 'Promo'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        new_cat = Category.objects.get(name='Marketing App')

        # Delete
        del_response = self.client.post(
            reverse('category_delete', args=[new_cat.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(del_response.status_code, 200)
        self.assertFalse(Category.objects.filter(id=new_cat.id).exists())

    def test_settings_clear_tasks_vs_clear_all(self):
        # Create second task
        Task.objects.create(user=self.user, title='Task to delete')

        # Test clear_tasks: Tasks should be deleted, projects should remain
        response = self.client.post(
            reverse('settings'),
            data={'action': 'clear_tasks', 'confirm_clear': 'yes'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 0)
        self.assertTrue(Category.objects.filter(id=self.project.id).exists())

        # Test clear_all: Both tasks and categories should be deleted
        Task.objects.create(user=self.user, title='Another Task')
        response_all = self.client.post(
            reverse('settings'),
            data={'action': 'clear_all', 'confirm_clear': 'yes'}
        )
        self.assertEqual(response_all.status_code, 302)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 0)
        self.assertEqual(Category.objects.filter(user=self.user).count(), 0)

    def test_ai_endpoints(self):
        # AI Suggest
        suggest_res = self.client.post(
            reverse('api_ai_suggest'),
            data=json.dumps({'prompt': 'Launch mobile website'}),
            content_type='application/json'
        )
        self.assertEqual(suggest_res.status_code, 200)
        self.assertTrue(suggest_res.json()['success'])

        # AI Create Task
        task_res = self.client.post(
            reverse('ai_create_task'),
            data=json.dumps({'title': 'AI Generated Task', 'description': 'Auto plan'}),
            content_type='application/json'
        )
        self.assertEqual(task_res.status_code, 200)
        self.assertTrue(Task.objects.filter(title='AI Generated Task').exists())

        # AI Create Project
        proj_res = self.client.post(
            reverse('ai_create_project'),
            data=json.dumps({'name': 'AI Project', 'tasks': ['Sub 1', 'Sub 2']}),
            content_type='application/json'
        )
        self.assertEqual(proj_res.status_code, 200)
        self.assertTrue(Category.objects.filter(name='AI Project').exists())
        self.assertEqual(Task.objects.filter(category__name='AI Project').count(), 2)

    def test_stats_and_export_api(self):
        stats_res = self.client.get(reverse('stats_api'))
        self.assertEqual(stats_res.status_code, 200)
        self.assertIn('total_count', stats_res.json()['stats'])

        export_json = self.client.get(reverse('tasks_export_api') + '?format=json')
        self.assertEqual(export_json.status_code, 200)
        self.assertIn('tasks', export_json.json())

        export_csv = self.client.get(reverse('tasks_export_api') + '?format=csv')
        self.assertEqual(export_csv.status_code, 200)
        self.assertEqual(export_csv['Content-Type'], 'text/csv; charset=utf-8')

    def test_kanban_and_manage_tasks_empty_state_without_projects(self):
        # Create a fresh user with no projects
        fresh_user = User.objects.create_user(username='emptyuser', password='password123')
        self.client.login(username='emptyuser', password='password123')

        kanban_res = self.client.get(reverse('manage_kanban'))
        self.assertEqual(kanban_res.status_code, 200)
        self.assertFalse(kanban_res.context['has_projects'])
        self.assertContains(kanban_res, 'No Projects Found')

        tasks_res = self.client.get(reverse('manage_tasks'))
        self.assertEqual(tasks_res.status_code, 200)
        self.assertFalse(tasks_res.context['has_projects'])
        self.assertContains(tasks_res, 'No Projects Found')

    def test_category_board_template_smart_vs_super(self):
        smart_proj = Category.objects.create(
            user=self.user,
            name='Smart Project',
            board_template=Category.BoardTemplate.SMART
        )
        super_proj = Category.objects.create(
            user=self.user,
            name='Super Project',
            board_template=Category.BoardTemplate.SUPER
        )

        self.assertEqual(len(smart_proj.get_board_columns()), 4)
        self.assertEqual(len(super_proj.get_board_columns()), 6)

        # Verify Kanban view loads columns accordingly
        res_smart = self.client.get(reverse('manage_kanban') + f'?project={smart_proj.id}')
        self.assertEqual(len(res_smart.context['active_columns']), 4)

        res_super = self.client.get(reverse('manage_kanban') + f'?project={super_proj.id}')
        self.assertEqual(len(res_super.context['active_columns']), 6)

    def test_category_rename_column_view(self):
        rename_res = self.client.post(
            reverse('category_rename_column', args=[self.project.id]),
            data=json.dumps({'column_key': 'not-started', 'title': 'Up Next'}),
            content_type='application/json'
        )
        self.assertEqual(rename_res.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.get_column_title('not-started'), 'Up Next')
