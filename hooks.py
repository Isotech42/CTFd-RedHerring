from sqlalchemy.event import listen
from CTFd.models import db, Teams, Challenges, Flags

from .utils import generate_flag, create_docker_container
from .models import Containers
from . import globals

def on_team_create(mapper, conn, team):
    # When a team is created, create a new flag for each challenge that is a "red_herring" type
    red_herring_challenges = Challenges.query.filter_by(type="red_herring").all()

    port = globals.PORT_CONTAINERS_START
    if len(red_herring_challenges) != 0:

        # Get the last port used
        last_container = Containers.query.order_by(Containers.port.desc()).first()
        if last_container is not None:
            port = last_container.port + 1

    for challenge in red_herring_challenges:
        generated_flag = generate_flag()

        # Create the flag
        flag = Flags(challenge_id = challenge.id, type = "red_herring", content = generated_flag, data = team.id)
        db.session.add(flag)

        # Create the container
        # Get the buildfile of the challenge
        buildfile = challenge.dockerfile

        # Generate the container
        container_name = create_docker_container(buildfile=buildfile, flag=generated_flag, port=port, challenge_name=challenge.name, team_id=team.id)

        # Save the container in the database
        container = Containers(name=container_name, port=port, dockerfile=buildfile, challengeid=challenge.id, teamid=team.id)
        port += 1
        db.session.add(container)

def load_hooks():
    listen(Teams, "after_insert", on_team_create)