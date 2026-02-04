import uuid

from django.shortcuts import render
from .models import Questionnaire, Question, Responses, QuestionnaireLog, Prospect

def prospect_form(request, questionnaire_id=None):
    if request.method == 'GET' and questionnaire_id:
        questionnaire = Questionnaire.objects.get(id=questionnaire_id) if questionnaire_id else None
        questions = questionnaire.questions.all() if questionnaire else []

        new_form_id = uuid.uuid4().hex.upper() if questionnaire else None

        log = QuestionnaireLog.objects.create(
            form_id=new_form_id,
            action='form_viewed'
        ) if questionnaire else None
        log.save()

        context = {
            'questionnaire': questionnaire,
            'questions': questions,
            'new_form_id': new_form_id,
        }
        return render(request, 'form.html', context)
    return render(request, 'error.html', {'message': 'Invalid request'})

def prospect_form_submit(request, questionnaire_id=None):
    if request.method == 'POST' and questionnaire_id:
        new_form_id = request.POST.get('new_form_id')
        questionnaire = Questionnaire.objects.get(id=questionnaire_id)

        logged = QuestionnaireLog.objects.filter(
            form_id=new_form_id,
            action='form_submitted',
        )

        if logged.count() > 0:
            # return render(request, 'error.html', {'message': 'Form already submitted'})
            return render(request, 'join.html', {'questionnaire': questionnaire, 'prospect_form_id': new_form_id})

        questions = questionnaire.questions.all()

        for question in questions:
            answer = request.POST.get(f'question_{question.id}', '')
            Responses.objects.create(
                question=question,
                answer_text=answer,
                prospect_form_id=new_form_id,
            )

        log = QuestionnaireLog.objects.create(
            form_id=new_form_id,
            action='form_submitted',
        )
        log.save()

        return render(request, 'join.html', {'questionnaire': questionnaire, 'prospect_form_id': new_form_id})

    return render(request, 'error.html', {'message': 'Invalid request'})

def prospect_join(request, prospect_form_id=None):
    if request.method == 'GET' and prospect_form_id:
        log = QuestionnaireLog.objects.create(
            form_id=prospect_form_id,
            action='prospect_signing_up',
        )
        log.save()
        return render(request, 'train.html', {'prospect_form_id': prospect_form_id})
    if request.method == 'POST' and prospect_form_id:
        log = QuestionnaireLog.objects.create(
            form_id=prospect_form_id,
            action='prospect_signed_up',
        )
        log.save()
        p = Prospect.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone_number=request.POST.get('phone'),
            prospect_form_id=prospect_form_id,
        )
        p.save()
        return render(request, 'success.html', {'prospect_form_id': prospect_form_id})
    return render(request, 'error.html', {'message': 'Invalid request'})

def prospect_no_join(request, prospect_form_id=None):
    if request.method == 'GET' and prospect_form_id:
        log = QuestionnaireLog.objects.create(
            form_id=prospect_form_id,
            action='prospect_declined',
        )
        log.save()
        return render(request, 'nojoin.html', {'prospect_form_id': prospect_form_id})
    return render(request, 'error.html', {'message': 'Invalid request'})

def prospect_join_self_study(request, prospect_form_id=None):
    if request.method == 'GET' and prospect_form_id:
        log = QuestionnaireLog.objects.create(
            form_id=prospect_form_id,
            action='prospect_self_study_signup',
        )
        log.save()
        return render(request, 'selfstudy.html', {'prospect_form_id': prospect_form_id, 'self_study': True})
    return render(request, 'error.html', {'message': 'Invalid request'})

def prospect_final_success(request, prospect_form_id=None):
    if request.method == 'GET' and prospect_form_id:
        log = QuestionnaireLog.objects.create(
            form_id=prospect_form_id,
            action='prospect_final_success',
        )
        log.save()
        return render(request, 'finalsuccess.html', {'prospect_form_id': prospect_form_id})
    return render(request, 'error.html', {'message': 'Invalid request'})