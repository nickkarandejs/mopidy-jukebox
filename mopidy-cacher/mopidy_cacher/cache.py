from mopidy import commands

class CacherCommand(commands.Command):
    help = 'Some text that will show up in --help'

    def __init__(self):
        super(CacherCommand, self).__init__()
        self.add_argument('--foo')

    def run(self, args, config):
        print(config["cacher"]["caches"])
        return 0
