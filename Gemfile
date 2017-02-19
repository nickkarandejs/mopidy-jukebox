source 'https://rubygems.org'
gem "chef", '~> 11.12'

gem 'berkshelf', '~> 4.0'

# Ruby 2.1 issues
gem 'buff-ignore', '<1.2.0'
gem 'rack', '<2.0.1'
gem 'nokogiri', '<1.7'

group :integration do
  gem 'test-kitchen', '~> 1.9', '>= 1.9.2'
  gem 'foodcritic', '<7.0'
end

group :docker do
  gem 'kitchen-dokken'
end
