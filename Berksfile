source "https://supermarket.chef.io"

cookbook 'mopidy-jukebox', path: 'cookbooks/mopidy-jukebox'
cookbook 'build-essential', '< 4.0.0' # 4.0 needs Chef 12
cookbook 'unattended-upgrades', '~> 0.1.2'

# Chef 11 fixes
cookbook 'apt', '<4'
cookbook 'yum-epel', '<1'
cookbook 'ohai', '<4'
cookbook 'yum', '<4'