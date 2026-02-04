from django.core.management.base import BaseCommand
from django.db import transaction
from prospect.models import Questionnaire, Question, Responses, SelectOption


class Command(BaseCommand):
    help = 'Seed database with 3 questionnaires, each with 5 questions and responses.'

    def handle(self, *args, **options):
        with transaction.atomic():
            created_qs = []
            for qidx in range(1, 4):
                name = f"questionnaire_{qidx}"
                title = f"Sample Questionnaire {qidx}"
                desc = f"Auto-generated sample questionnaire {qidx}."
                questionnaire = Questionnaire.objects.create(name=name, title=title, description=desc)
                created_qs.append(questionnaire)

                # choose two orders to be 'select' type
                select_orders = {2, 4}
                for order in range(1, 6):
                    q_type = 'select' if order in select_orders else 'text'
                    q_text = f"Question {order} for {title}"
                    question = Question.objects.create(
                        questionnaire=questionnaire,
                        text=q_text,
                        type=q_type,
                        order=order,
                    )

                    # create select options for select questions
                    if q_type == 'select':
                        opts = ['Option A', 'Option B', 'Option C']
                        for idx, opt_text in enumerate(opts, start=1):
                            SelectOption.objects.create(
                                question=question,
                                text=opt_text,
                                value=opt_text,
                                order=idx,
                            )

                # create one response per question for this questionnaire
                prospect_form_id = f"sample_form_{qidx}"
                for question in questionnaire.questions.all():
                    if question.type == 'select':
                        answer = 'Option A'
                    else:
                        answer = f"Sample answer for {question.text}"
                    Responses.objects.create(
                        question=question,
                        answer_text=answer,
                        prospect_form_id=prospect_form_id,
                    )

            self.stdout.write(self.style.SUCCESS(f"Created {len(created_qs)} questionnaires with questions and responses."))
