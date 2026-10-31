"""Public, paginated question browsing. Answers remain in the normal practice flow."""
from math import ceil
from typing import Literal
from urllib.parse import urlencode

from fastapi import Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from . import services
from .i18n import client_strings, t
from .models import Question, Subject, Topic

PAGE_SIZE = 30


def install_routes(app, render, get_db, lang_from_request):
    def public_page(template, request, lang, **extra):
        language = lang or lang_from_request(request)
        response = render(template, request, None, lang=language,
                          tr=lambda key: t(key, language),
                          L=lambda hi, en: hi if language == 'hi' else en,
                          strings=client_strings(language), **extra)
        # Only these intentionally anonymous pages may enter the phone's reading cache.
        response.headers['X-SS-Public-Content'] = 'questions-v1'
        return response

    @app.get('/questions', response_class=HTMLResponse)
    def question_bank(request: Request, subject: str = Query('', max_length=40),
                      topic: str = Query('', pattern=r'^(?:[1-9][0-9]{0,9})?$'),
                      level: str = Query('', max_length=20),
                      difficulty: str = Query('', max_length=10),
                      q: str = Query('', max_length=120),
                      page: int = Query(1, ge=1, le=10000),
                      lang: Literal['hi', 'en'] | None = None,
                      db: Session = Depends(get_db)):
        topic = int(topic) if topic else None
        if level not in ('', '10th', '12th', 'graduate') or difficulty not in ('', 'easy', 'medium', 'hard'):
            raise HTTPException(422, 'invalid_question_filter')
        subjects = list(db.scalars(select(Subject).options(selectinload(Subject.topics)).order_by(Subject.id)))
        if subject and subject not in {s.slug for s in subjects}:
            raise HTTPException(404, 'subject')
        if topic and topic not in {tp.id for s in subjects for tp in s.topics}:
            raise HTTPException(404, 'topic')
        filters = [services.USABLE]
        if subject:
            filters.append(Topic.subject_id == next(s.id for s in subjects if s.slug == subject))
        if topic:
            filters.append(Question.topic_id == topic)
        if level:
            filters.append(Question.level == level)
        if difficulty:
            filters.append(Question.difficulty == difficulty)
        search = q.strip()
        if search:
            filters.append(or_(Question.text_hi.contains(search, autoescape=True),
                               Question.text_en.contains(search, autoescape=True)))
        filtered = bool(subject or topic or level or difficulty or search)
        total = (db.scalar(select(func.count(Question.id)).join(Topic).where(*filters))
                 if filtered else sum(services.recent_topic_counts(db).values()))
        pages = max(1, ceil(total / PAGE_SIZE))
        if page > pages:
            raise HTTPException(404, 'question_page')
        questions = list(db.scalars(select(Question).join(Topic).where(*filters)
                                   .options(joinedload(Question.topic).joinedload(Topic.subject))
                                   .order_by(Question.id).offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)))
        language = lang or lang_from_request(request)
        params = {'subject': subject, 'level': level, 'difficulty': difficulty, 'q': search, 'lang': language}
        if topic:
            params['topic'] = topic
        def page_url(number):
            return '/questions?' + urlencode({**params, 'page': number})
        return public_page('question_bank.html', request, lang, subjects=subjects, questions=questions,
                           selected_subject=subject, selected_topic=topic, selected_level=level,
                           selected_difficulty=difficulty, search=search, total=total, page=page,
                           pages=pages, previous=page_url(page - 1) if page > 1 else None,
                           following=page_url(page + 1) if page < pages else None)

    @app.get('/questions/{question_id}', response_class=HTMLResponse)
    def question_detail(question_id: int, request: Request, lang: Literal['hi', 'en'] | None = None,
                        db: Session = Depends(get_db)):
        question = db.scalar(select(Question).where(Question.id == question_id, services.USABLE)
                             .options(joinedload(Question.topic).joinedload(Topic.subject)))
        if question is None:
            raise HTTPException(404, 'question')
        language = lang or lang_from_request(request)
        text = question.text_hi if language == 'hi' else question.text_en
        options = question.options_hi if language == 'hi' else question.options_en
        fallback = not text
        if fallback:
            text = question.text_en if language == 'hi' else question.text_hi
            options = question.options_en if language == 'hi' else question.options_hi
        return public_page('question_detail.html', request, lang, question=question,
                           question_text=text, question_options=options or [], fallback=fallback)
