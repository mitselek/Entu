from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images
from google.appengine.api import users
from django.utils import simplejson
import datetime
import random
import string

from bo import *
from database.application import *
from database.person import *
from database.zimport.zgeneral import *
from libraries.gmemsess import *


class ShowSignin(boRequestHandler):
    def get(self):

        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/application/signin'))

        sess = Session(self, timeout=86400)
        sess.invalidate()

        self.view('application', 'application/signup.html', {
            'account_login_url': users.create_login_url('/application'),
        })

    def post(self):

        email = self.request.get('email').strip()
        password = self.request.get('applicant_pass').strip()

        if email:
            p = db.Query(Person).filter('email', email).get()
            if not p:
                p = db.Query(Person).filter('apps_username', email).get()
                if not p:
                    p = Person()
                    p.email = email
                    p.idcode = ''
                    p.model_version = 'SSS'
                    p.put()

                    c = Contact(parent=p)
                    c.type = 'email'
                    c.value = email
                    c.put()

            password = ''.join(random.choice(string.ascii_letters) for x in range(2))
            password += str(p.key().id())
            password += ''.join(random.choice(string.ascii_letters) for x in range(3))
            password = password.replace('O', random.choice(string.ascii_lowercase))

            p.password = password
            p.put()

            if SendMail(
                to = email,
                subject = Translate('application_signup_mail_subject'),
                message = Translate('application_signup_mail_message') % p.password
            ):
                self.response.out.write('OK')

        else:
            if password:
                p = db.Query(Person).filter('password', password).get()
                if p:
                    sess = Session(self, timeout=86400)
                    sess['application_person_key'] = p.key()
                    sess.save()
                    self.response.out.write('OK')


class ShowApplication(boRequestHandler):
    def get(self):

        p =  Person().current_s(self)
        now = datetime.now()

        if not p:
            self.redirect('/application/signin')
        else:
            receptions = []
            application_submitted = False
            for reception in db.Query(Reception).order('end_date').fetch(1000):
                a = db.Query(Application).ancestor(p).filter('reception', reception).get()
                receptions.append({'reception': reception, 'application': a})
                if a:
                    if a.status == 'submitted':
                        application_submitted = True

            photo_upload_url = blobstore.create_upload_url('/document/upload')
            document_upload_url = blobstore.create_upload_url('/document/upload')
            documents = db.Query(Document).filter('entities', str(p.key())).filter('types', 'application_document').fetch(1000)
            secondaryschools = db.Query(Cv).ancestor(p).filter('type', 'secondary_education').fetch(1000)
            highschools = db.Query(Cv).ancestor(p).filter('type', 'higher_education').fetch(1000)
            workplaces = db.Query(Cv).ancestor(p).filter('type', 'workplace').fetch(1000)

            self.view('application', 'application/application.html', {
                'application_submitted': application_submitted,
                'receptions': receptions,
                'person': p,
                'date_days': range(1, 32),
                'date_months': Translate('list_months').split(','),
                'document_types': Translate('application_documents_types').split(','),
                'date_years': range((now.year-15), (now.year-90), -1),
                'photo_upload_url': photo_upload_url,
                'document_upload_url': document_upload_url,
                'documents': documents,
                'secondaryschools': secondaryschools,
                'highschools': highschools,
                'workplaces': workplaces,
            })

    def post(self):
        p =  Person().current_s(self)
        if p:
            key = self.request.get('key').strip()
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            respond = {}

            r = Reception().get(key)
            if r:
                a = db.Query(Application).ancestor(p).filter('reception', r).get()
                if not a:
                    a = Application(parent=p)
                    a.reception = r

                if field == 'selected':
                    if value.lower() == 'true':
                        a.status = 'selected'
                    else:
                        a.status = 'unselected'

                if field == 'comment':
                    a.comment = value

                a.put()

            respond['key'] = key
            self.response.out.write(simplejson.dumps(respond))


class SubmitApplication(boRequestHandler):
    def get(self):
        p =  Person().current_s(self)
        if p:
            selected = False
            for a in db.Query(Application).ancestor(p).filter('status', 'selected').fetch(1000):
                a.status = 'submitted'
                a.put()
                selected = True
                SendMail(
                    to = a.reception.communication_email,
                    subject = Translate('application_submit_email1_subject') % p.displayname,
                    message = Translate('application_submit_email1_message') % {'name': p.displayname, 'link': SYSTEM_URL + '/reception/' + str(p.key()) }
                )

            if selected:
                emails = []
                if p.email:
                    emails = AddToList(p.email, emails)
                if p.apps_username:
                    emails = AddToList(p.apps_username, emails)
                for contact in db.Query(Contact).ancestor(p).filter('type', 'email').fetch(1000):
                    emails = AddToList(contact.value, emails)

                SendMail(
                    to = emails,
                    subject = Translate('application_submit_email2_subject') % p.displayname,
                    message = Translate('application_submit_email2_message')
                )

                sess = Session(self, timeout=86400)
                sess.invalidate()
                self.redirect(users.create_logout_url('/application/thanks'))

            else:
                self.redirect('/application')
                return


class ShowSubmitApplication(boRequestHandler):
    def get(self):
        self.view('application', 'application/submitted.html', {
            'message': Translate('application_submit_success_message')
        })


class EditPerson(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            respond = {}

            if field in ['forename', 'surname', 'idcode', 'gender']:
                setattr(p, field, value)

            if field == 'birthdate':
                if value:
                    p.birth_date = datetime.strptime(value, '%d.%m.%Y').date()
                else:
                    p.birth_date = None

            if field == 'have_been_subsidised':
                if value.lower() == 'true':
                    p.have_been_subsidised = True
                else:
                    p.have_been_subsidised = False

            p.put()
            self.response.out.write(simplejson.dumps(respond))


class EditContact(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            key = self.request.get('key').strip()
            type = self.request.get('type').strip()
            value = self.request.get('value').strip()
            respond = {}

            if key:
                c = Contact().get(key)
                if value:
                    c.type = type
                    c.value = value
                    c.put()
                    response_key = str(c.key())
                else:
                    c.delete()
                    response_key = ''
            else:
                c = Contact(parent=p)
                c.type = type
                c.value = value
                c.put()
                response_key = str(c.key())

            respond['key'] = response_key

            p.put()
            self.response.out.write(simplejson.dumps(respond))


class EditCV(boRequestHandler):
    def post(self):
        p =  Person().current_s(self)
        if p:
            key = self.request.get('key').strip()
            field = self.request.get('field').strip()
            value = self.request.get('value').strip()
            type = self.request.get('type').strip()
            respond = {}

            if key:
                cv = Cv().get(key)
            else:
                cv = Cv(parent=p)
                cv.type = type

            if field in ['organisation','start', 'end', 'description']:
                setattr(cv, field, value)

            cv.put()
            respond['key'] = str(cv.key())

            self.response.out.write(simplejson.dumps(respond))


def main():
    Route([
            ('/application', ShowApplication),
            ('/application/signin', ShowSignin),
            ('/application/person', EditPerson),
            ('/application/contact', EditContact),
            ('/application/cv', EditCV),
            ('/application/submit', SubmitApplication),
            ('/application/thanks', ShowSubmitApplication),
        ])


if __name__ == '__main__':
    main()