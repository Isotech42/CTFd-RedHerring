import os
import json
from flask import render_template, Blueprint
from flask import request, jsonify,session

from CTFd.models import (
    Awards,
    ChallengeFiles,
    Challenges,
    Fails,
    Flags,
    Hints,
    Solves,
    Tags,
    Teams,
    db,
)

from .hooks import load_hooks
from .models import CheaterTeams, RedHerringChallenge, Containers
from .utils import generate_flag, create_docker_container
from . import globals

from CTFd.plugins import register_plugin_assets_directory
from CTFd.plugins.migrations import upgrade
from CTFd.plugins.challenges import BaseChallenge, CHALLENGE_CLASSES
from CTFd.plugins.flags import FlagException, get_flag_class, CTFdStaticFlag, FLAG_CLASSES
from CTFd.utils.uploads import delete_file
from CTFd.utils.user import get_current_team, get_current_user
from CTFd.utils.decorators import admins_only
from CTFd.config import Config


PLUGIN_PATH = os.path.dirname(__file__)
CONFIG = json.load(open("{}/config.json".format(PLUGIN_PATH)))

red = Blueprint('red_herring', __name__, template_folder="templates")

class RedHerringTypeChallenge(BaseChallenge):
    id = "red_herring"  # Unique identifier used to register challenges
    name = "red_herring"  # Name of a challenge type
    templates = {  # Nunjucks templates used for each aspect of challenge editing & viewing
        'create': '/plugins/red_herring/assets/create.html',  # Used to render the challenge when creating/editing
        'update': '/plugins/red_herring/assets/update.html',  # Used to render the challenge when updating
        'view': '/plugins/red_herring/assets/view.html',  # Used to render the challenge when viewing
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        'create': '/plugins/red_herring/assets/create.js',  # Used to init the create template JavaScript
        'update': '/plugins/red_herring/assets/update.js',  # Used to init the create template JavaScript
        'view': '/plugins/red_herring/assets/view.js',  # Used to init the create template JavaScript
    }

    # Route at which files are accessible. This must be registered using register_plugin_assets_directory()
    route = "/plugins/red_herring/assets/"
    challenge_model = RedHerringChallenge
    
    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.

        :param request:
        :return:
        """
        data = request.form or request.get_json()
        challenge = RedHerringChallenge(
            name=data['name'],
            category=data['category'],
            description=data['description'],
            value=data['value'],
            state=data['state'],
            type=data['type'],
        )
        buildfile = data['buildfile']

        db.session.add(challenge)
        db.session.commit()

        # Check if there is teams that are created
        teams = Teams.query.all()
        if len(teams) > 0:
            # For each team, create a flag and a container for the challenge
            for team in teams:
                generated_flag = generate_flag()
                
                port = globals.PORT_CONTAINERS_START

                # Generate the container
                container_name = create_docker_container(buildfile=buildfile, flag=generated_flag, port=port, challenge_name=challenge.name, team_id=team.id)

                # Save the container in the database
                container = Containers(name=container_name, port=port, dockerfile=buildfile, challengeid=challenge.id, teamid=team.id)
                db.session.add(container)
                globals.PORT_CONTAINERS_START += 1

                # Save the flag in the database
                flag = Flags(challenge_id = challenge.id, type = "red_herring", content = generated_flag, data = team.id)
                db.session.add(flag)

            db.session.commit()
        
        return challenge

class RedHearingFlag(CTFdStaticFlag):
    name = "red_herring"

    @staticmethod
    def compare(chal_key_obj, provided_flag):
        # Get the actual flag to check for the challenge submitted (the function compare() is called for each flag of the challenge)
        saved_flag = chal_key_obj.content

        # Compare each character in the flag if the team id is the one that is supposed to solve the challenge
        curr_team_id = get_current_team().id

        result = 0
        for x, y in zip(saved_flag, provided_flag):
            result |= ord(x) ^ ord(y)
        
        if result == 0:
            # If the flag is correct, we need to check if the team is the one associated with the flag
            team_id_needed = chal_key_obj.data
            if int(team_id_needed) == int(curr_team_id):
                return True
            else:
                curr_user_id = get_current_user().id
                cheater = CheaterTeams(challengeid=chal_key_obj.challenge_id, cheaterid=curr_user_id, cheatteamid=curr_team_id, sharerteamid=team_id_needed, flagid=chal_key_obj.id)
                db.session.add(cheater)
                return False
        else:
            print("wrong flag")
            return False


@red.route('/admin/red_herring',methods=['GET'])
@admins_only
def show_cheaters():
    if request.method == 'GET':
        cheaters = CheaterTeams.query.all()
        return render_template('red_herring.html', cheaters=cheaters)


def load(app):
    globals.initialize()
    app.db.create_all() # Create all DB entities
    upgrade(plugin_name="red_herring")

    CHALLENGE_CLASSES['red_herring'] = RedHerringTypeChallenge
    FLAG_CLASSES['red_herring'] = RedHearingFlag

    app.register_blueprint(red)
    register_plugin_assets_directory(app, base_path="/plugins/red_herring/assets/")

    load_hooks()