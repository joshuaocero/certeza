from django.contrib.auth.models import User
from django.db import models

class Organisation(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class AppUser(models.Model):
    organisation = models.ForeignKey(Organisation, related_name='users', on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[
        ('admin', 'Admin'),
        ('discipler', 'Discipler'),
        ('trainee', 'Trainee'),
    ])
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

class DisciplerProfile(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='discipler_profiles/', blank=True, null=True)
    trainings_completed = models.ManyToManyField('Training', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Discipler Profile for {self.user.username}"

class Training(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    organisations = models.ManyToManyField(Organisation, related_name='trainings', blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TraineeProfile(models.Model):
    user = models.OneToOneField(AppUser, on_delete=models.CASCADE)
    enrolled_training = models.ForeignKey(Training, related_name='trainees', on_delete=models.CASCADE)
    status = models.CharField(max_length=50, choices=[
        ('enrolled', 'Enrolled'),
        ('in_progress', 'In Progress'),
        ('stalled', 'Stalled'),
        ('completed', 'Completed'),
        ('dropped', 'Dropped'),
    ], default='enrolled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Trainee Profile for {self.user.username}"

class Prospect(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    prospect_form_id = models.CharField(max_length=100, unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    discipler = models.ForeignKey(DisciplerProfile, related_name='prospects', on_delete=models.SET_NULL, blank=True, null=True)
    organisation = models.ForeignKey(Organisation, related_name='prospects', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ActiveQuestionnaire(models.Model):
    organisation = models.ForeignKey(Organisation, related_name='active_questionnaires', on_delete=models.CASCADE)
    questionnaire = models.ForeignKey('prospect.Questionnaire', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    deactivated_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Active Questionnaire {self.questionnaire.name} for {self.organisation.name}"

class DiscipleshipPaths(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='discipleship_path_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    trainings = models.ManyToManyField(Training, related_name='discipleship_paths', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class DiscipleshipPathsAssignment(models.Model):
    prospect = models.ForeignKey(Prospect, related_name='discipleship_assignments', on_delete=models.CASCADE)
    discipleship_path = models.ForeignKey(DiscipleshipPaths, related_name='assignments', on_delete=models.CASCADE)
    completion_status = models.CharField(max_length=50, choices=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('stalled', 'Stalled'),
        ('completed', 'Completed'),
    ], default='not_started')
    assigned_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prospect.name} assigned to {self.discipleship_path.name}"

class DiscipleshipFollowUp(models.Model):
    prospect = models.ForeignKey(Prospect, related_name='follow_ups', on_delete=models.CASCADE)
    discipler = models.ForeignKey(DisciplerProfile, related_name='follow_ups', on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)
    follow_up_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Follow-up for {self.prospect.name} by {self.discipler.user.username}"

class Configs(models.Model):
    config_key = models.CharField(max_length=100, unique=True)
    config_value = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.config_key
