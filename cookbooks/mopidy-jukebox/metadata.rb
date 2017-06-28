name             'mopidy-jukebox'
maintainer       'Tom Parker'
maintainer_email 'palfrey@tevp.net'
license          'GNU Affero General Public License, Version 3'
description      'Installs/Configures mopidy-jukebox'
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version          '0.1.0'
issues_url 'https://github.com/palfrey/mopidy-jukebox/issues' if respond_to?(:issues_url)
source_url 'https://github.com/palfrey/mopidy-jukebox' if respond_to?(:source_url)

depends 'python'
depends 'build-essential'
depends 'unattended-upgrades'
