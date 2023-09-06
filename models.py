from CTFd.models import db, Teams, Challenges, Flags
from CTFd.utils.user import get_current_team
from . import globals

class RedHerringChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "red_herring"}
    id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True
    )
    dockerfile = db.Column(db.Text)

    def __init__(self, *args, **kwargs):
        super(RedHerringChallenge, self).__init__(**kwargs)
        self.dockerfile = kwargs["dockerfile"]

    def get_container_port(self):
        try :
            teamid = get_current_team().id
        except:
            teamid = None
        
        if teamid is None:
            return None
        
        container = Containers.query.filter_by(challengeid=self.id, teamid=teamid).first()
        return container.port
    
    def get_container_address(self):
        return globals.IP_ADDRESS_CONTAINERS


class CheaterTeams(db.Model):
    __tablename__ = 'cheater_teams'

    id = db.Column(db.Integer, primary_key=True)
    challengeid = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete="CASCADE"))
    cheaterid = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"))
    cheatteamid = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete="CASCADE"))
    sharerteamid = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete="CASCADE"))
    flagid = db.Column(db.Integer, db.ForeignKey('flags.id', ondelete="CASCADE"))
    date = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, challengeid, cheaterid, cheatteamid, sharerteamid, flagid):
        self.challengeid = challengeid
        self.cheaterid = cheaterid
        self.cheatteamid = cheatteamid
        self.sharerteamid = sharerteamid
        self.flagid = flagid

    def __repr__(self):
        return "<CheaterTeams Team {0} maybe cheated for challenge {1} with the flag {2} belonging to the team {3} at {4} >".format(self.cheatteamid, self.challengeid, self.flagid, self.sharerteamid, self.date)
    
    def cheated_team_name(self):
        return Teams.query.filter_by(id=self.cheatteamid).first().name

    def shared_team_name(self):
        return Teams.query.filter_by(id=self.sharerteamid).first().name

    def challenge_name(self):
        return Challenges.query.filter_by(id=self.challengeid).first().name
    
    def flag_content(self):
        return Flags.query.filter_by(id=self.flagid).first().content

class Containers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    dockerfile = db.Column(db.Text)
    address = db.Column(db.String(80))
    port = db.Column(db.Integer)
    challengeid = db.Column(db.Integer, db.ForeignKey('challenges.id', ondelete="CASCADE"))
    teamid = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete="CASCADE"))

    def __init__(self, challengeid, teamid, name, dockerfile, port, address="127.0.0.1"):
        self.name = name
        self.dockerfile = dockerfile
        self.challengeid = challengeid
        self.teamid = teamid
        self.port = port
        self.address = globals.IP_ADDRESS_CONTAINERS

    def __repr__(self):
        return "<Container ID:(0) {1} for the challenge {2} and the team {3}>".format(self.id, self.name, self.challengeid, self.teamid)