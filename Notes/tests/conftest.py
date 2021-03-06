import os
import pytest
import random
import string
import tempfile

from ..apps.users.models import Role
from ..apps.users import services as user_services
from ..apps.notes import services as note_services

from ..authentication import services as auth_services
''' 
configures the application for testing and initializes a new database
https://flask.palletsprojects.com/en/1.1.x/testing/	the-testing-skeleton
'''
# init db

# FIXTURES: SESSION
@pytest.fixture(scope='session')
def app():
	from .. import app
	from ..config import TestingConfig
	app.config.from_object(TestingConfig)
	
	return app

@pytest.fixture(scope='session')
def client(app):
	with app.test_client() as client:
		yield client	


@pytest.fixture(scope='session')
def db(app):	
	from .. import db
	with app.app_context():
		db.create_all()
		yield db

		#CLEAN UP
		db.drop_all()
		 
	os.remove(
		app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///',''))	

# FIXTURES: CLASS
@pytest.fixture(scope='class')
def db_session(app, db):
	# Use flush() instead of commit() to
	# communicate with the database while testing

	with app.app_context():
		yield db.session

		#CLEAN UP
		db.session.rollback()
		db.session.close()

# FIXTURES: FUNCTION
@pytest.fixture(scope='function')
def test_user(db_session):
	if not user_services.get_role({'name':'user'}):
		# do not use has_access 1 for 'user' role in production
		db_session.add(Role(name='user', has_full_access=1))
		db_session.commit()

	rdm_name = random_str('name')
	user_data = {'name': rdm_name, 
				 'email': (rdm_name + '@email.com'),
				 'password': rdm_name}
				
	user = user_services.create_user(**user_data)

	ret = {
		'access_token_fresh': auth_services.create_access_token(identity=user.public_id, fresh=True),
		'access_token': auth_services.create_access_token(identity=user.public_id, fresh=False),
		'refresh_token': auth_services.create_refresh_token(identity=user.public_id)}

	return user, {**user_data, **ret}

@pytest.fixture(scope='function')
def test_user_note(test_user):
	user, user_data = test_user

	if not note_services.get_note_type({'name':'note'}):
		note_services.create_type('note')

	note = note_services.create_note(
		user_public_id=user.public_id,
		tag_list=['music'],
		text=random_str('note'))
	return user, user_data, note

@pytest.fixture(scope='function')
def test_user_tag(test_user):
	user, user_data = test_user

	tag = note_services.create_tag(
		user_public_id=user.public_id, name=random_str('tag'))
	return user, user_data, tag


@pytest.fixture(scope='function')
def test_user_type(test_user):
	user, user_data = test_user

	_type = note_services.create_type(random_str('type'))
	return user, user_data, _type

def random_str(prefix):
	return (
		prefix +'_' + 
		''.join(random.choice(string.ascii_lowercase) for l in range(10))
	)