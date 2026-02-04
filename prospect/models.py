from django.db import models


class Questionnaire(models.Model):
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s - %s" % (self.name, self.title)

class Question(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField()
    type = models.CharField(max_length=20, choices=[
        ('text', 'Text'),
        ('select', 'Select'),
    ])
    order = models.PositiveIntegerField()

    def __str__(self):
        return "Question %d: %s" % (self.order, self.text)

class SelectOption(models.Model):
    questions = models.ManyToManyField(Question, related_name='options')
    text = models.CharField(max_length=200)
    value = models.CharField(max_length=200, blank=True, null=True)
    order = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Option for %s" % (self.text)

class Responses(models.Model):
    question = models.ForeignKey(Question, related_name='responses', on_delete=models.CASCADE)
    answer_text = models.TextField(blank=True, null=True)
    prospect_form_id = models.CharField(max_length=100, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Response to %s - %s at %s" % (self.question.questionnaire.name, self.question.text, self.submitted_at)

class QuestionnaireLog(models.Model):
    form_id = models.CharField(max_length=200)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Log for %s at %s" % (self.form_id, self.timestamp)

class Prospect(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    prospect_form_id = models.CharField(max_length=100, unique=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name