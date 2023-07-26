from mnemonic import Mnemonic
import docker
import tempfile
from . import globals

def generate_flag():
    mnemo = Mnemonic(globals.FLAG_LANGUAGE)
    words = mnemo.generate(strength=128)

    # Take only the first 4 words
    words = words.split(" ")[0:4]

    # Insert the header of the flag and "_" between words like "flag{word1_word2_word3_word4}"
    flag = globals.FLAG_PREFIX + "{" + "_".join(words) + "}"
    return flag

def create_docker_container(buildfile, flag, port, challenge_name, team_id):
    # Convert the buildfile (which is a string) to a new temporary File object
    temp_dockerfile = tempfile.TemporaryFile()
    temp_dockerfile.write(buildfile.encode())
    temp_dockerfile.seek(0)

    # Create a Docker client
    client = docker.from_env()

    # Build image from Dockerfile
    challenge_name = challenge_name.replace(" ", "_")
    tag_name = (challenge_name).lower()
    my_image = client.images.build(fileobj=temp_dockerfile, tag=tag_name)

    # Run container from image
    container = client.containers.run(  image=tag_name,
                                        detach=True,
                                        tty=True,
                                        environment=["FLAG=" + flag],
                                        command="/bin/bash",
                                        ports={'80/tcp':(globals.IP_ADDRESS_CONTAINERS,port)},
                                        )
    temp_dockerfile.close()

    return container.name