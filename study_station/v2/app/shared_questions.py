"""Anonymous, answer-free shared questions, using an explicit public field allowlist."""
from typing import Literal

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import services
from .config import ANDROID_APP_PACKAGE
from .i18n import client_strings, t
from .models import Question, Subject, Topic


def install_routes(app, render, get_db, lang_from_request):
    @app.get('/q/{question_id}', response_class=HTMLResponse)
    def shared_question(question_id: int, request: Request,
                        lang: Literal['hi', 'en'] | None = None,
                        db: Session = Depends(get_db)):
        # Do not load the ORM Question: the rendering path must never receive its answer.
        row = db.execute(select(
            Question.id, Question.text_hi, Question.text_en,
            Question.options_hi, Question.options_en,
            Topic.name_hi.label('topic_hi'), Topic.name_en.label('topic_en'),
            Subject.name_hi.label('subject_hi'), Subject.name_en.label('subject_en'),
        ).join(Topic, Question.topic_id == Topic.id)
          .join(Subject, Topic.subject_id == Subject.id)
          .where(Question.id == question_id, services.USABLE)).mappings().first()
        if row is None:
            raise HTTPException(404, 'question')
        language = lang or lang_from_request(request)
        fallback = not row['text_' + language]
        content_language = ('en' if language == 'hi' else 'hi') if fallback else language
        public = {
            'id': row['id'], 'code': f'SS-{row["id"]}',
            'text': row['text_' + content_language] or '',
            'options': row['options_' + content_language] or [],
            'topic': row['topic_' + language], 'subject': row['subject_' + language],
        }
        response = render('shared_question.html', request, None, lang=language,
                          tr=lambda key: t(key, language),
                          L=lambda hi, en: hi if language == 'hi' else en,
                          strings=client_strings(language), shared=public, fallback=fallback,
                          app_intent=(f'intent://studystation.ebookcart.in/q/{row["id"]}?lang={language}'
                                      f'#Intent;scheme=https;package={ANDROID_APP_PACKAGE};end')
                          if ANDROID_APP_PACKAGE in ('com.studystation.app', 'com.studystation.app.debug') else None)
        response.headers['X-SS-Public-Content'] = 'shared-question-v1'
        # An explicit language is cacheable; cookie-selected language must not cross users.
        response.headers['Cache-Control'] = 'public, max-age=300' if lang else 'no-store'
        return response
