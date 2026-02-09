from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import (Organisation, Prospect, DiscipleshipFollowUp, DisciplerProfile,
                     DiscipleshipPathsAssignment, Configs, TraineeProfile, Training)
from .models import ActiveQuestionnaire
from prospect.models import Responses, Questionnaire
import json

def home(request):
    if request.user.is_authenticated:
        try:
            app_user = request.user.appuser
            organisation = app_user.organisation
        except:
            organisation = Organisation.objects.first()
    else:
        organisation = Organisation.objects.first()
    
    if not organisation:
        return render(request, 'home.html', {})
    
    # Get last visit time from session
    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit = timezone.datetime.fromisoformat(last_visit)
    else:
        last_visit = timezone.now() - timedelta(days=30)  # Default to 30 days ago
    
    # Set current visit time
    request.session['last_visit'] = timezone.now().isoformat()
    
    # ===== PROSPECTS DATA =====
    total_prospects = Prospect.objects.filter(organisation=organisation).count()
    new_prospects = Prospect.objects.filter(
        organisation=organisation,
        created_at__gte=last_visit
    ).count()
    
    # ===== QUESTIONNAIRES & RESPONSES DATA =====
    active_questionnaires = ActiveQuestionnaire.objects.filter(
        organisation=organisation,
        is_active=True
    ).select_related('questionnaire')
    
    questionnaire_data = []
    total_responses = 0
    new_responses = 0
    
    for aq in active_questionnaires:
        q = aq.questionnaire
        all_responses = Responses.objects.filter(
            question__questionnaire=q
        ).values('prospect_form_id').distinct().count()
        
        responses_since_visit = Responses.objects.filter(
            question__questionnaire=q,
            submitted_at__gte=last_visit
        ).values('prospect_form_id').distinct().count()
        
        total_responses += all_responses
        new_responses += responses_since_visit
        
        questionnaire_data.append({
            'name': q.name,
            'title': q.title,
            'total_responses': all_responses,
            'new_responses': responses_since_visit,
        })
    
    # ===== DISCIPLESHIP FOLLOW-UPS DATA =====
    due_followups = DiscipleshipFollowUp.objects.filter(
        prospect__organisation=organisation,
        follow_up_date__lte=timezone.now(),
        follow_up_date__isnull=False
    ).select_related('prospect', 'discipler', 'discipler__user').order_by('follow_up_date')
    
    context = {
        'total_prospects': total_prospects,
        'new_prospects': new_prospects,
        'total_responses': total_responses,
        'new_responses': new_responses,
        'questionnaire_data': questionnaire_data,
        'due_followups': due_followups,
        'organisation': organisation,
    }
    
    return render(request, 'home.html', context)

def dashboard(request):
    if request.user.is_authenticated:
        try:
            app_user = request.user.appuser
            organisation = app_user.organisation
        except:
            organisation = Organisation.objects.first()
    else:
        organisation = Organisation.objects.first()
    
    if not organisation:
        return render(request, 'dashboard.html', {})
    
    # ===== PROSPECT ACCEPTANCE RATE =====
    # Count prospects with at least one survey response (accepted)
    prospects_with_responses = Prospect.objects.filter(
        organisation=organisation
    ).annotate(
        response_count=Count('responses', distinct=True)
    ).filter(response_count__gt=0).count()
    
    total_prospects = Prospect.objects.filter(organisation=organisation).count()
    acceptance_rate = (prospects_with_responses / total_prospects * 100) if total_prospects > 0 else 0
    
    acceptance_data = {
        'accepted': prospects_with_responses,
        'pending': total_prospects - prospects_with_responses,
        'rate': round(acceptance_rate, 1)
    }
    
    # ===== PROSPECT ASSIGNMENT RATE =====
    # Count prospects assigned to disciplers
    assigned_prospects = Prospect.objects.filter(
        organisation=organisation,
        discipler__isnull=False
    ).count()
    
    unassigned_prospects = total_prospects - assigned_prospects
    assignment_rate = (assigned_prospects / total_prospects * 100) if total_prospects > 0 else 0
    
    assignment_data = {
        'assigned': assigned_prospects,
        'unassigned': unassigned_prospects,
        'rate': round(assignment_rate, 1)
    }
    
    # ===== DISCIPLESHIP COMPLETION RATE =====
    # Count prospects with completed discipleship paths
    completed_assignments = DiscipleshipPathsAssignment.objects.filter(
        prospect__organisation=organisation,
        completion_status='completed'
    ).count()
    
    total_assignments = DiscipleshipPathsAssignment.objects.filter(
        prospect__organisation=organisation
    ).count()
    
    completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
    
    discipleship_data = {
        'completed': completed_assignments,
        'in_progress': DiscipleshipPathsAssignment.objects.filter(
            prospect__organisation=organisation,
            completion_status='in_progress'
        ).count(),
        'not_started': DiscipleshipPathsAssignment.objects.filter(
            prospect__organisation=organisation,
            completion_status='not_started'
        ).count(),
        'stalled': DiscipleshipPathsAssignment.objects.filter(
            prospect__organisation=organisation,
            completion_status='stalled'
        ).count(),
        'rate': round(completion_rate, 1)
    }
    
    # ===== SURVEY RESPONSES OVER PAST WEEK =====
    week_ago = timezone.now() - timedelta(days=7)
    daily_responses = {}
    
    for i in range(7):
        date = timezone.now().date() - timedelta(days=6-i)
        day_start = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.min.time()))
        day_end = timezone.make_aware(timezone.datetime.combine(date, timezone.datetime.max.time()))
        
        count = Responses.objects.filter(
            question__questionnaire__activequestionnaire__organisation=organisation,
            submitted_at__gte=day_start,
            submitted_at__lte=day_end
        ).count()
        
        daily_responses[date.strftime('%a')] = count
    
    # ===== DISCIPLER-PROSPECT RATIO =====
    total_disciplers = DisciplerProfile.objects.filter(
        user__organisation=organisation
    ).count()
    
    # Get recommended ratio from configs
    try:
        ratio_config = Configs.objects.get(config_key='discipler_prospect_ratio')
        recommended_ratio = float(ratio_config.config_value)
    except:
        recommended_ratio = 1.0  # Default 1:1 or 1:5 depending on preference
    
    current_ratio = (total_prospects / total_disciplers) if total_disciplers > 0 else 0
    
    ratio_data = {
        'current': round(current_ratio, 1),
        'recommended': recommended_ratio,
        'total_disciplers': total_disciplers,
        'total_prospects': total_prospects,
        'health': 'healthy' if current_ratio <= recommended_ratio else 'overloaded'
    }
    
    # ===== TRAINING COMPLETION RATES =====
    trainings = Training.objects.filter(organisations=organisation)
    training_data = []
    
    for training in trainings:
        total_trainees = TraineeProfile.objects.filter(enrolled_training=training).count()
        completed_trainees = TraineeProfile.objects.filter(
            enrolled_training=training,
            status='completed'
        ).count()
        
        completion_rate = (completed_trainees / total_trainees * 100) if total_trainees > 0 else 0
        
        training_data.append({
            'name': training.name,
            'total_trainees': total_trainees,
            'completed': completed_trainees,
            'completion_rate': round(completion_rate, 1),
            'in_progress': TraineeProfile.objects.filter(
                enrolled_training=training,
                status='in_progress'
            ).count(),
        })
    
    # ===== ADDITIONAL METRICS =====
    # Average responses per questionnaire
    active_questionnaires = ActiveQuestionnaire.objects.filter(
        organisation=organisation,
        is_active=True
    )
    
    total_questionnaire_responses = 0
    for aq in active_questionnaires:
        count = Responses.objects.filter(
            question__questionnaire=aq.questionnaire
        ).values('prospect_form_id').distinct().count()
        total_questionnaire_responses += count
    
    avg_responses_per_questionnaire = (
        total_questionnaire_responses / active_questionnaires.count()
    ) if active_questionnaires.count() > 0 else 0
    
    context = {
        'organisation': organisation,
        'acceptance_data': acceptance_data,
        'assignment_data': assignment_data,
        'discipleship_data': discipleship_data,
        'daily_responses': json.dumps(daily_responses),
        'ratio_data': ratio_data,
        'training_data': training_data,
        'avg_responses_per_questionnaire': round(avg_responses_per_questionnaire, 1),
        'total_questionnaires': active_questionnaires.count(),
    }
    
    return render(request, 'dashboard.html', context)

def prospects(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    if request.user.is_authenticated:
        try:
            app_user = request.user.appuser
            organisation = app_user.organisation
        except:
            organisation = Organisation.objects.first()
    else:
        organisation = Organisation.objects.first()
    
    if not organisation:
        return render(request, 'prospects.html', {})
    
    # Get the active tab
    tab = request.GET.get('tab', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    prospects_qs = Prospect.objects.filter(organisation=organisation).select_related('discipler')
    
    # Filter by tab
    if tab == 'assigned':
        prospects_qs = prospects_qs.filter(discipler__isnull=False)
    elif tab == 'unassigned':
        prospects_qs = prospects_qs.filter(discipler__isnull=True)
    
    # Search across all fields
    if search_query:
        prospects_qs = prospects_qs.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(prospect_form_id__icontains=search_query)
        )
    
    # Sort by creation date (newest first)
    prospects_qs = prospects_qs.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(prospects_qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get counts for tabs
    all_count = Prospect.objects.filter(organisation=organisation).count()
    assigned_count = Prospect.objects.filter(organisation=organisation, discipler__isnull=False).count()
    unassigned_count = Prospect.objects.filter(organisation=organisation, discipler__isnull=True).count()
    
    # Get available disciplers for assignment
    available_disciplers = DisciplerProfile.objects.filter(user__organisation=organisation)
    
    context = {
        'page_obj': page_obj,
        'prospects': page_obj.object_list,
        'tab': tab,
        'search_query': search_query,
        'all_count': all_count,
        'assigned_count': assigned_count,
        'unassigned_count': unassigned_count,
        'available_disciplers': available_disciplers,
        'organisation': organisation,
    }
    
    return render(request, 'prospects.html', context)

def assign_prospect(request):
    """AJAX endpoint to assign a prospect to a discipler"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        prospect_id = request.POST.get('prospect_id')
        discipler_id = request.POST.get('discipler_id')
        
        try:
            prospect = Prospect.objects.get(id=prospect_id)
            discipler = DisciplerProfile.objects.get(id=discipler_id)
            
            prospect.discipler = discipler
            prospect.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{prospect.name} assigned to {discipler.user.first_name} {discipler.user.last_name}'
            })
        except Prospect.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Prospect not found'})
        except DisciplerProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Discipler not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def disciplers(request):
    from django.core.paginator import Paginator
    from django.db.models import Count, Q
    
    if request.user.is_authenticated:
        try:
            app_user = request.user.appuser
            organisation = app_user.organisation
        except:
            organisation = Organisation.objects.first()
    else:
        organisation = Organisation.objects.first()
    
    if not organisation:
        return render(request, 'disciplers.html', {})
    
    # Get the active tab
    tab = request.GET.get('tab', 'all')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    disciplers_qs = DisciplerProfile.objects.filter(
        user__organisation=organisation
    ).select_related('user').prefetch_related('trainings_completed', 'prospects')
    
    # Filter by tab (training status)
    if tab == 'trained':
        # Disciplers who have completed at least one training
        disciplers_qs = disciplers_qs.annotate(
            training_count=Count('trainings_completed')
        ).filter(training_count__gt=0)
    elif tab == 'not_trained':
        # Disciplers who have not completed any training
        disciplers_qs = disciplers_qs.annotate(
            training_count=Count('trainings_completed')
        ).filter(training_count=0)
    
    # Search across all fields
    if search_query:
        disciplers_qs = disciplers_qs.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    
    # Sort by last name (alphabetically)
    disciplers_qs = disciplers_qs.order_by('user__last_name', 'user__first_name')
    
    # Pagination
    paginator = Paginator(disciplers_qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get counts for tabs
    all_count = DisciplerProfile.objects.filter(user__organisation=organisation).count()
    trained_count = DisciplerProfile.objects.filter(
        user__organisation=organisation
    ).annotate(training_count=Count('trainings_completed')).filter(training_count__gt=0).count()
    not_trained_count = all_count - trained_count
    
    # Get unassigned prospects for assignment modal
    unassigned_prospects = Prospect.objects.filter(
        organisation=organisation,
        discipler__isnull=True
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'disciplers': page_obj.object_list,
        'tab': tab,
        'search_query': search_query,
        'all_count': all_count,
        'trained_count': trained_count,
        'not_trained_count': not_trained_count,
        'unassigned_prospects': unassigned_prospects,
        'organisation': organisation,
    }
    
    return render(request, 'disciplers.html', context)

def assign_prospect_to_discipler(request):
    """AJAX endpoint to assign a prospect to a discipler from disciplers page"""
    from django.http import JsonResponse
    
    if request.method == 'POST':
        discipler_id = request.POST.get('discipler_id')
        prospect_id = request.POST.get('prospect_id')
        
        try:
            discipler = DisciplerProfile.objects.get(id=discipler_id)
            prospect = Prospect.objects.get(id=prospect_id)
            
            prospect.discipler = discipler
            prospect.save()
            
            return JsonResponse({
                'success': True,
                'message': f'{prospect.name} assigned to {discipler.user.first_name} {discipler.user.last_name}'
            })
        except DisciplerProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Discipler not found'})
        except Prospect.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Prospect not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def survey_responses(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    if request.user.is_authenticated:
        try:
            app_user = request.user.appuser
            organisation = app_user.organisation
        except:
            organisation = Organisation.objects.first()
    else:
        organisation = Organisation.objects.first()
    
    if not organisation:
        return render(request, 'responses.html', {})
    
    search_query = request.GET.get('search', '')
    
    # Base queryset - get responses filtered by active questionnaires in the organisation
    responses_qs = Responses.objects.filter(
        question__questionnaire__activequestionnaire__organisation=organisation
    ).select_related('question', 'question__questionnaire').order_by('-submitted_at')
    
    # Search across relevant fields
    if search_query:
        responses_qs = responses_qs.filter(
            Q(prospect_form_id__icontains=search_query) |
            Q(question__questionnaire__name__icontains=search_query) |
            Q(question__text__icontains=search_query) |
            Q(answer_text__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(responses_qs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get total counts
    total_responses = Responses.objects.filter(
        question__questionnaire__activequestionnaire__organisation=organisation
    ).count()
    
    context = {
        'page_obj': page_obj,
        'responses': page_obj.object_list,
        'search_query': search_query,
        'total_responses': total_responses,
        'organisation': organisation,
    }
    
    return render(request, 'responses.html', context)